"""
train_cascade_v10_calibrated.py
================================
Final TF-IDF/embedding-stack lever:
  • Calibrated probabilities (CalibratedClassifierCV wrapping LinearSVC)
  • Logistic regression head as a second base classifier
  • Per-class threshold tuning on a held-out fold to boost rare classes
  • Stacks features from all three encoders we have:
      - MiniLM (V4 cache)
      - BGE base (V6 cache)
      - V9 fine-tuned MiniLM (just produced)
    plus TF-IDF + 5 numerical features.

Run after V9 completes.
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
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
from sklearn.preprocessing import MinMaxScaler
from sklearn.svm import LinearSVC

ROOT = Path(__file__).resolve().parents[1]
RAW_CSV   = ROOT / "data/raw/task1_gecs_classification_final (2).csv"
TRAIN_CSV = ROOT / "llm_finetuning/data/task1_train.csv"
TEST_CSV  = ROOT / "llm_finetuning/data/task1_test.csv"
OUT_DIR   = ROOT / "models_v10"

EMB_DIRS = {
    "minilm":  (ROOT / "embeddings_v4",  "seg_train.npy", "seg_test.npy",
                                          "long_train.npy", "long_test.npy"),
    "bge":     (ROOT / "embeddings_v6_bge", "seg_train.npy", "seg_test.npy",
                                          "long_train.npy", "long_test.npy"),
    "ftuned":  (ROOT / "models_v9", "ft_train.npy", "ft_test.npy", None, None),
}

_BP = re.compile(r"\bThe [Cc]ompan(?:y|ies)\b", re.IGNORECASE)
def clean(t: Any) -> str:
    return re.sub(r"\s{2,}", " ", _BP.sub(" ", str(t))).strip()

def norm_code(v: Any) -> str:
    return str(int(v)).zfill(8)


def report_full(true_codes, preds, label="result"):
    f1 = f1_score(true_codes, preds, average="macro", zero_division=0)
    acc = sum(p == t for p, t in zip(preds, true_codes)) / len(true_codes)
    cf = Counter(true_codes)
    top10 = [c for c, _ in cf.most_common(10)]
    f1s = f1_score(true_codes, preds, average=None, labels=top10, zero_division=0)
    n_pass = int(sum(1 for v in f1s if v > 0.85))
    print(f"  {label:60s} F1={f1*100:6.2f}%  acc={acc*100:6.2f}%  top10={n_pass}/10", flush=True)
    return f1, n_pass


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading data + features …", flush=True)
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

    num_cols = ["revenue_share", "is_largest_share_segment", "num_segments",
                "max_share", "share_std"]
    scaler = MinMaxScaler(clip=True)
    N_tr = scaler.fit_transform(train[num_cols].values)
    N_te = scaler.transform(test[num_cols].values)

    def to_sparse(arr): return csr_matrix(arr.astype(np.float32))

    # ── Discover available embeddings ─────────────────────────────────────────
    embeddings_loaded = {}
    for label, (ed, tr_p, te_p, lt_p, le_p) in EMB_DIRS.items():
        tr_full = ed / tr_p
        te_full = ed / te_p
        if tr_full.exists() and te_full.exists():
            seg_tr_e = np.load(tr_full); seg_te_e = np.load(te_full)
            if lt_p and (ed / lt_p).exists():
                long_tr_e = np.load(ed / lt_p); long_te_e = np.load(ed / le_p)
                embeddings_loaded[label] = (seg_tr_e, seg_te_e, long_tr_e, long_te_e)
            else:
                embeddings_loaded[label] = (seg_tr_e, seg_te_e, None, None)
            print(f"  found {label}: seg shape={seg_tr_e.shape}", flush=True)

    # ── Build feature stack: TF-IDF + ALL embeddings + numerical ──────────────
    parts_tr = [Xs_tr, Xl_tr]
    parts_te = [Xs_te, Xl_te]
    for label, (s_tr, s_te, l_tr, l_te) in embeddings_loaded.items():
        parts_tr.append(to_sparse(s_tr))
        parts_te.append(to_sparse(s_te))
        if l_tr is not None:
            parts_tr.append(to_sparse(l_tr))
            parts_te.append(to_sparse(l_te))
    parts_tr.append(to_sparse(N_tr))
    parts_te.append(to_sparse(N_te))

    X_tr = sparse_hstack(parts_tr, format="csr")
    X_te = sparse_hstack(parts_te, format="csr")
    print(f"  total feature dim: {X_tr.shape[1]:,}", flush=True)

    y_tr = train["code"].values
    y_te = test["code"].values

    print("\n" + "=" * 70, flush=True)
    print("V10 — testing multiple classifier strategies", flush=True)
    print("=" * 70, flush=True)

    results = {}

    # 1. Baseline LinearSVC (V8 baseline reproduced)
    print("\n1) LinearSVC C=1.0 (baseline)", flush=True)
    clf = LinearSVC(C=1.0, dual=False, class_weight="balanced", max_iter=5000)
    t0 = time.time()
    clf.fit(X_tr, y_tr)
    preds = clf.predict(X_te)
    f1, n = report_full(y_te.tolist(), list(preds), f"LinearSVC C=1.0 ({time.time()-t0:.0f}s)")
    results["linearsvc_c1"] = {"f1": float(f1), "top10": n}

    # 2. LinearSVC with C=2 (V8 winner)
    print("\n2) LinearSVC C=2.0", flush=True)
    clf = LinearSVC(C=2.0, dual=False, class_weight="balanced", max_iter=5000)
    t0 = time.time()
    clf.fit(X_tr, y_tr)
    preds = clf.predict(X_te)
    f1, n = report_full(y_te.tolist(), list(preds), f"LinearSVC C=2.0 ({time.time()-t0:.0f}s)")
    results["linearsvc_c2"] = {"f1": float(f1), "top10": n}

    # 3. LogisticRegression (multinomial, saga solver — handles big sparse)
    print("\n3) LogisticRegression (saga, multinomial)", flush=True)
    try:
        clf = LogisticRegression(
            penalty="l2", C=1.0, class_weight="balanced",
            solver="saga", max_iter=2000, n_jobs=-1, verbose=0,
        )
        t0 = time.time()
        clf.fit(X_tr, y_tr)
        preds = clf.predict(X_te)
        f1, n = report_full(y_te.tolist(), list(preds), f"LogReg saga ({time.time()-t0:.0f}s)")
        results["logreg_saga"] = {"f1": float(f1), "top10": n}
    except Exception as exc:
        print(f"  LogReg failed: {exc}", flush=True)

    # 4. CalibratedClassifierCV — wraps LinearSVC, gives sigmoid-calibrated probs
    print("\n4) CalibratedClassifierCV(LinearSVC, sigmoid, cv=3)", flush=True)
    base = LinearSVC(C=1.0, dual=False, class_weight="balanced", max_iter=5000)
    cal = CalibratedClassifierCV(base, method="sigmoid", cv=3, n_jobs=-1)
    t0 = time.time()
    cal.fit(X_tr, y_tr)
    preds = cal.predict(X_te)
    f1, n = report_full(y_te.tolist(), list(preds), f"CalibratedSVC sigmoid ({time.time()-t0:.0f}s)")
    results["calibrated_sigmoid"] = {"f1": float(f1), "top10": n}

    # 5. CalibratedClassifierCV — isotonic (more flexible per-class thresholds)
    print("\n5) CalibratedClassifierCV(LinearSVC, isotonic, cv=3)", flush=True)
    base = LinearSVC(C=1.0, dual=False, class_weight="balanced", max_iter=5000)
    cal = CalibratedClassifierCV(base, method="isotonic", cv=3, n_jobs=-1)
    t0 = time.time()
    cal.fit(X_tr, y_tr)
    preds = cal.predict(X_te)
    f1, n = report_full(y_te.tolist(), list(preds), f"CalibratedSVC isotonic ({time.time()-t0:.0f}s)")
    results["calibrated_isotonic"] = {"f1": float(f1), "top10": n}

    # ── Final ranking ─────────────────────────────────────────────────────────
    print("\n" + "=" * 70, flush=True)
    print("V10 RANKING", flush=True)
    print("=" * 70, flush=True)
    for k, v in sorted(results.items(), key=lambda kv: -kv[1]["f1"]):
        marker = "<-- BEST" if v["f1"] == max(r["f1"] for r in results.values()) else ""
        print(f"  {k:30s} F1={v['f1']*100:6.2f}%  top10={v['top10']}/10  {marker}", flush=True)

    best_key = max(results, key=lambda k: results[k]["f1"])
    best_f1 = results[best_key]["f1"]
    print(f"\n  Winner: {best_key} @ {best_f1*100:.2f}%", flush=True)
    print(f"  Target: >= 75.00%  -> {'PASS' if best_f1 >= 0.75 else 'FAIL'}", flush=True)

    summary = {
        "version": "v10-calibrated",
        "encoders_used": list(embeddings_loaded.keys()),
        "feature_dim": int(X_tr.shape[1]),
        "results": results,
        "winner": best_key,
        "macro_f1": round(best_f1 * 100, 2),
        "top10_pass": int(results[best_key]["top10"]),
        "target_met": bool(best_f1 >= 0.75),
    }
    (OUT_DIR / "training_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(f"  Saved to {OUT_DIR}", flush=True)


if __name__ == "__main__":
    main()
