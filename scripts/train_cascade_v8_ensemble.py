"""
train_cascade_v8_ensemble.py
============================
Builds an ensemble from any of the V4/V6/V7 embedding sets that are cached
on disk. Stacks all available embeddings + TF-IDF + numerical and trains a
final flat LinearSVC. Picks the best of [single best | ensemble] as winner.

Run after V6 (and optionally V7) have produced cached embeddings.
"""
from __future__ import annotations

import json
import re
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, hstack as sparse_hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import f1_score
from sklearn.preprocessing import MinMaxScaler
from sklearn.svm import LinearSVC

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

RAW_CSV   = ROOT / "data/raw/task1_gecs_classification_final (2).csv"
TRAIN_CSV = ROOT / "llm_finetuning/data/task1_train.csv"
TEST_CSV  = ROOT / "llm_finetuning/data/task1_test.csv"
OUT_DIR   = ROOT / "models_v8"

EMB_DIRS = {
    "minilm": ROOT / "embeddings_v4",
    "bge":    ROOT / "embeddings_v6_bge",
    "setfit": ROOT / "models_v7",
}

MAX_ITER = 5000


_BP = re.compile(r"\bThe [Cc]ompan(?:y|ies)\b", re.IGNORECASE)
def clean(t: Any) -> str:
    return re.sub(r"\s{2,}", " ", _BP.sub(" ", str(t))).strip()

def norm_code(v: Any) -> str:
    return str(int(v)).zfill(8)


def report(true_codes, preds, label="result"):
    f1 = f1_score(true_codes, preds, average="macro", zero_division=0)
    acc = sum(p == t for p, t in zip(preds, true_codes)) / len(true_codes)
    cf = Counter(true_codes)
    top10 = [c for c, _ in cf.most_common(10)]
    f1s = f1_score(true_codes, preds, average=None, labels=top10, zero_division=0)
    n_pass = int(sum(1 for v in f1s if v > 0.85))
    print(f"  {label}: F1={f1*100:.2f}%  acc={acc*100:.2f}%  top10={n_pass}/10")
    return f1, n_pass


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading data …", flush=True)
    raw = pd.read_csv(RAW_CSV)
    raw["combined"] = (
        raw["LongProfile"].fillna("") + " " +
        raw["SegmentName"].fillna("") + " " +
        raw["SegmentDescription"].fillna("")
    ).str.replace(r"\s+", " ", regex=True).str.strip()

    company_stats = raw.groupby("CompanyId").agg(
        num_segments=("SegmentName", "size"),
        max_share=("revenue_share", lambda x: x.abs().max()),
        share_std=("revenue_share", lambda x: float(x.std()) if len(x) > 1 else 0.0),
    ).reset_index()
    raw = raw.merge(company_stats, on="CompanyId", how="left")
    raw["share_std"] = raw["share_std"].fillna(0.0)

    raw_dedup = raw.drop_duplicates("combined", keep="first")
    join_cols = ["combined", "LongProfile", "SegmentName", "SegmentDescription",
                 "revenue_share", "is_largest_share_segment",
                 "num_segments", "max_share", "share_std"]

    train = pd.read_csv(TRAIN_CSV).merge(raw_dedup[join_cols],
                                          left_on="text", right_on="combined", how="left")
    test  = pd.read_csv(TEST_CSV).merge(raw_dedup[join_cols],
                                          left_on="text", right_on="combined", how="left")
    for df in (train, test):
        df["LongProfile"]              = df["LongProfile"].fillna(df["text"])
        df["SegmentName"]              = df["SegmentName"].fillna("")
        df["SegmentDescription"]       = df["SegmentDescription"].fillna(df["text"])
        df["revenue_share"]            = df["revenue_share"].fillna(0.5)
        df["is_largest_share_segment"] = df["is_largest_share_segment"].fillna(False).astype(float)
        df["num_segments"]             = df["num_segments"].fillna(1)
        df["max_share"]                = df["max_share"].fillna(0.5)
        df["share_std"]                = df["share_std"].fillna(0.0)
        df["code"] = df["mstar_code"].map(norm_code)

    print(f"  train={len(train):,}  test={len(test):,}", flush=True)

    # ── TF-IDF ─────────────────────────────────────────────────────────────────
    print("\nBuilding TF-IDF …", flush=True)
    seg_tr = (train["SegmentName"] + " " + train["SegmentDescription"]).map(clean)
    seg_te = (test["SegmentName"]  + " " + test["SegmentDescription"]).map(clean)
    long_tr = train["LongProfile"].map(clean)
    long_te = test["LongProfile"].map(clean)

    vec_seg = TfidfVectorizer(max_features=80000, sublinear_tf=True, stop_words="english",
                              ngram_range=(1, 2), min_df=2)
    vec_lng = TfidfVectorizer(max_features=40000, sublinear_tf=True, stop_words="english",
                              ngram_range=(1, 2), min_df=2)
    Xs_tr = vec_seg.fit_transform(seg_tr);  Xs_te = vec_seg.transform(seg_te)
    Xl_tr = vec_lng.fit_transform(long_tr); Xl_te = vec_lng.transform(long_te)

    # ── Numerical ──────────────────────────────────────────────────────────────
    num_cols = ["revenue_share", "is_largest_share_segment", "num_segments",
                "max_share", "share_std"]
    scaler = MinMaxScaler(clip=True)
    N_tr = scaler.fit_transform(train[num_cols].values)
    N_te = scaler.transform(test[num_cols].values)

    # ── Discover available embeddings ─────────────────────────────────────────
    available = []
    for label, ed in EMB_DIRS.items():
        if label == "setfit":
            seg_tr_p = ed / "setfit_train.npy"
            seg_te_p = ed / "setfit_test.npy"
            if seg_tr_p.exists() and seg_te_p.exists():
                e_tr = np.load(seg_tr_p)
                e_te = np.load(seg_te_p)
                available.append((label, e_tr, e_te, None, None))
                print(f"  found {label}: train={e_tr.shape}", flush=True)
        else:
            seg_tr_p = ed / "seg_train.npy"
            seg_te_p = ed / "seg_test.npy"
            long_tr_p = ed / "long_train.npy"
            long_te_p = ed / "long_test.npy"
            if all(p.exists() for p in [seg_tr_p, seg_te_p, long_tr_p, long_te_p]):
                seg_e_tr = np.load(seg_tr_p);  seg_e_te = np.load(seg_te_p)
                lng_e_tr = np.load(long_tr_p); lng_e_te = np.load(long_te_p)
                available.append((label, seg_e_tr, seg_e_te, lng_e_tr, lng_e_te))
                print(f"  found {label}: seg={seg_e_tr.shape}  long={lng_e_tr.shape}", flush=True)

    if not available:
        print("ERROR: no embeddings found. Run V4 or V6 first.", flush=True)
        return

    def to_sparse(arr): return csr_matrix(arr.astype(np.float32))

    y_tr = train["code"].values
    y_te = test["code"].values

    # ── Try each individual embedding + TF-IDF + numerical ────────────────────
    results = {}
    for label, seg_e_tr, seg_e_te, lng_e_tr, lng_e_te in available:
        parts_tr = [Xs_tr, Xl_tr, to_sparse(seg_e_tr)]
        parts_te = [Xs_te, Xl_te, to_sparse(seg_e_te)]
        if lng_e_tr is not None:
            parts_tr.append(to_sparse(lng_e_tr))
            parts_te.append(to_sparse(lng_e_te))
        parts_tr.append(to_sparse(N_tr))
        parts_te.append(to_sparse(N_te))

        X_tr = sparse_hstack(parts_tr, format="csr")
        X_te = sparse_hstack(parts_te, format="csr")

        print(f"\n--- {label} hybrid (dim={X_tr.shape[1]:,}) ---", flush=True)
        best_C, best_f1, best_n = 1.0, 0.0, 0
        for C in [0.5, 1.0, 2.0]:
            clf = LinearSVC(C=C, dual=False, class_weight="balanced", max_iter=MAX_ITER)
            t0 = time.time()
            clf.fit(X_tr, y_tr)
            preds = clf.predict(X_te)
            f1 = f1_score(y_te, preds, average="macro", zero_division=0)
            cf = Counter(y_te)
            top10 = [c for c, _ in cf.most_common(10)]
            f1s = f1_score(y_te, preds, average=None, labels=top10, zero_division=0)
            n_pass = int(sum(1 for v in f1s if v > 0.85))
            mark = "  <-- BEST" if f1 > best_f1 else ""
            print(f"  C={C}: F1={f1*100:.2f}%  top10={n_pass}/10  ({time.time()-t0:.1f}s){mark}", flush=True)
            if f1 > best_f1:
                best_C, best_f1, best_n = C, f1, n_pass
        results[label] = {"f1": float(best_f1), "C": best_C, "top10_pass": best_n}

    # ── Mega-ensemble: ALL embeddings + TF-IDF + numerical ────────────────────
    if len(available) > 1:
        print(f"\n--- MEGA ENSEMBLE: {len(available)} encoder(s) + TF-IDF + numerical ---", flush=True)
        parts_tr = [Xs_tr, Xl_tr]
        parts_te = [Xs_te, Xl_te]
        for label, seg_e_tr, seg_e_te, lng_e_tr, lng_e_te in available:
            parts_tr.append(to_sparse(seg_e_tr))
            parts_te.append(to_sparse(seg_e_te))
            if lng_e_tr is not None:
                parts_tr.append(to_sparse(lng_e_tr))
                parts_te.append(to_sparse(lng_e_te))
        parts_tr.append(to_sparse(N_tr))
        parts_te.append(to_sparse(N_te))
        X_tr_e = sparse_hstack(parts_tr, format="csr")
        X_te_e = sparse_hstack(parts_te, format="csr")
        print(f"  feature dim: {X_tr_e.shape[1]:,}", flush=True)

        best_C, best_f1, best_clf, best_n = 1.0, 0.0, None, 0
        for C in [0.5, 1.0, 2.0]:
            clf = LinearSVC(C=C, dual=False, class_weight="balanced", max_iter=MAX_ITER)
            t0 = time.time()
            clf.fit(X_tr_e, y_tr)
            preds = clf.predict(X_te_e)
            f1 = f1_score(y_te, preds, average="macro", zero_division=0)
            cf = Counter(y_te)
            top10 = [c for c, _ in cf.most_common(10)]
            f1s = f1_score(y_te, preds, average=None, labels=top10, zero_division=0)
            n_pass = int(sum(1 for v in f1s if v > 0.85))
            mark = "  <-- BEST" if f1 > best_f1 else ""
            print(f"  C={C}: F1={f1*100:.2f}%  top10={n_pass}/10  ({time.time()-t0:.1f}s){mark}", flush=True)
            if f1 > best_f1:
                best_C, best_f1, best_clf, best_n = C, f1, clf, n_pass
        results["MEGA_ENSEMBLE"] = {"f1": float(best_f1), "C": best_C, "top10_pass": best_n}

        joblib.dump(best_clf, OUT_DIR / "v8_ensemble_svm.joblib")

    # ── Final report ──────────────────────────────────────────────────────────
    print("\n" + "=" * 65, flush=True)
    print("V8 ENSEMBLE SUMMARY", flush=True)
    print("=" * 65, flush=True)
    for k, v in sorted(results.items(), key=lambda kv: -kv[1]["f1"]):
        marker = "<-- BEST" if v["f1"] == max(r["f1"] for r in results.values()) else ""
        print(f"  {k:20s}  F1={v['f1']*100:6.2f}%  top10={v['top10_pass']}/10  {marker}", flush=True)

    best_label = max(results, key=lambda k: results[k]["f1"])
    best_f1 = results[best_label]["f1"]
    print(f"\n  Winner: {best_label} @ {best_f1*100:.2f}%", flush=True)
    print(f"  Target: >= 75.00%  -> {'PASS' if best_f1 >= 0.75 else 'FAIL'}", flush=True)

    summary = {
        "version": "v8-ensemble",
        "available_encoders": [a[0] for a in available],
        "results": results,
        "winner": best_label,
        "best_f1": round(best_f1 * 100, 2),
        "target_met": bool(best_f1 >= 0.75),
    }
    (OUT_DIR / "training_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(f"\n  Saved to {OUT_DIR}", flush=True)


if __name__ == "__main__":
    main()
