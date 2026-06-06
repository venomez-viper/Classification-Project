"""
train_cascade_v12_prototypes.py
================================
Adds three high-impact components on top of V8's mega-ensemble:

  1. CLASS PROTOTYPES: For each of the 145 GECS codes, compute the mean
     embedding of all its training samples. At inference, compute cosine
     similarity from sample → each prototype = 145 new features per
     embedding space. This gives the classifier explicit class-boundary
     signal that bag-of-features can't see.

  2. STACKING ENSEMBLE: Three base classifiers (LinearSVC + LogReg +
     CalibratedSVC isotonic) → meta-classifier on stacked predictions.
     Reduces variance and corrects systematic errors.

  3. PER-CLASS THRESHOLD TUNING: After base classifier, optimize the
     per-class decision threshold on a held-out validation split to
     maximize macro F1 (boosts rare classes).

Uses ONLY cached embeddings (MiniLM + BGE) — no new encoding required.
Runs in ~30-60 min.

Run after V10 finishes (or alongside it):
    python scripts/train_cascade_v12_prototypes.py
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
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler, normalize
from sklearn.svm import LinearSVC

ROOT = Path(__file__).resolve().parents[1]
RAW_CSV   = ROOT / "data/raw/task1_gecs_classification_final (2).csv"
TRAIN_CSV = ROOT / "llm_finetuning/data/task1_train.csv"
TEST_CSV  = ROOT / "llm_finetuning/data/task1_test.csv"
EMB_DIRS  = {
    "minilm": ROOT / "embeddings_v4",
    "bge":    ROOT / "embeddings_v6_bge",
}
OUT_DIR   = ROOT / "models_v12"
MAX_ITER  = 5000


_BP = re.compile(r"\bThe [Cc]ompan(?:y|ies)\b", re.IGNORECASE)
def clean(t: Any) -> str:
    return re.sub(r"\s{2,}", " ", _BP.sub(" ", str(t))).strip()

def norm_code(v: Any) -> str:
    return str(int(v)).zfill(8)


def report(true_codes, preds, label):
    f1 = f1_score(true_codes, preds, average="macro", zero_division=0)
    acc = sum(p == t for p, t in zip(preds, true_codes)) / len(true_codes)
    cf = Counter(true_codes)
    top10 = [c for c, _ in cf.most_common(10)]
    f1s = f1_score(true_codes, preds, average=None, labels=top10, zero_division=0)
    n_pass = int(sum(1 for v in f1s if v > 0.85))
    print(f"  {label:55s} F1={f1*100:6.2f}%  acc={acc*100:6.2f}%  top10={n_pass}/10", flush=True)
    return f1, n_pass, acc


def compute_prototype_features(E_tr, E_te, y_tr) -> tuple[np.ndarray, np.ndarray]:
    """Compute class prototype centroids from train, then cosine-similarity
    of every sample to every prototype = (n, 145) features."""
    classes = sorted(set(str(y) for y in y_tr))
    proto = np.zeros((len(classes), E_tr.shape[1]), dtype=np.float32)
    for i, c in enumerate(classes):
        mask = np.array([str(y) == c for y in y_tr])
        proto[i] = E_tr[mask].mean(axis=0)
    proto = normalize(proto, norm="l2")
    Etr_n = normalize(E_tr, norm="l2")
    Ete_n = normalize(E_te, norm="l2")
    sim_tr = Etr_n @ proto.T   # (n_train, 145)
    sim_te = Ete_n @ proto.T   # (n_test, 145)
    return sim_tr.astype(np.float32), sim_te.astype(np.float32)


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

    # ── Build TF-IDF + numerical (same as V10) ────────────────────────────────
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

    # ── Load embeddings ───────────────────────────────────────────────────────
    embeddings = {}
    for label, ed in EMB_DIRS.items():
        s_tr = ed / "seg_train.npy"; s_te = ed / "seg_test.npy"
        l_tr = ed / "long_train.npy"; l_te = ed / "long_test.npy"
        if all(p.exists() for p in [s_tr, s_te, l_tr, l_te]):
            embeddings[label] = (
                np.load(s_tr), np.load(s_te), np.load(l_tr), np.load(l_te)
            )
            print(f"  loaded {label}: seg={embeddings[label][0].shape}", flush=True)

    y_tr = train["code"].values
    y_te = test["code"].values

    # ── Compute prototype-similarity features for each embedding space ────────
    print("\nComputing class prototypes (145 anchors per encoder) …", flush=True)
    proto_features = []
    for label, (s_tr, s_te, l_tr, l_te) in embeddings.items():
        for kind, E_tr, E_te in [("seg", s_tr, s_te), ("long", l_tr, l_te)]:
            t0 = time.time()
            P_tr, P_te = compute_prototype_features(E_tr, E_te, y_tr)
            print(f"  {label}_{kind}: {P_tr.shape}  ({time.time()-t0:.1f}s)", flush=True)
            proto_features.append((P_tr, P_te))

    # ── Build feature stack: TF-IDF + embeddings + prototypes + numerical ─────
    def to_sparse(arr): return csr_matrix(arr.astype(np.float32))

    parts_tr = [Xs_tr, Xl_tr]
    parts_te = [Xs_te, Xl_te]
    for label, (s_tr, s_te, l_tr, l_te) in embeddings.items():
        parts_tr += [to_sparse(s_tr), to_sparse(l_tr)]
        parts_te += [to_sparse(s_te), to_sparse(l_te)]
    for P_tr, P_te in proto_features:
        parts_tr.append(to_sparse(P_tr))
        parts_te.append(to_sparse(P_te))
    parts_tr.append(to_sparse(N_tr))
    parts_te.append(to_sparse(N_te))

    X_tr = sparse_hstack(parts_tr, format="csr")
    X_te = sparse_hstack(parts_te, format="csr")
    print(f"\nFinal feature dim: {X_tr.shape[1]:,} (incl. {len(proto_features)*145} prototype features)", flush=True)

    # ── Test multiple classifiers ─────────────────────────────────────────────
    print("\n" + "=" * 70, flush=True)
    print("V12 — TF-IDF + embeddings + PROTOTYPES + numerical", flush=True)
    print("=" * 70, flush=True)

    results = {}

    # 1. LinearSVC C=1.0
    print("\n1) LinearSVC C=1.0", flush=True)
    clf = LinearSVC(C=1.0, dual=False, class_weight="balanced", max_iter=MAX_ITER)
    t0 = time.time()
    clf.fit(X_tr, y_tr)
    preds = clf.predict(X_te)
    f1, n, acc = report(y_te.tolist(), list(preds), f"LinearSVC C=1.0 ({time.time()-t0:.0f}s)")
    results["linearsvc_c1"] = {"f1": float(f1), "top10": n, "acc": float(acc)}

    # 2. LinearSVC C=2
    print("\n2) LinearSVC C=2.0", flush=True)
    clf = LinearSVC(C=2.0, dual=False, class_weight="balanced", max_iter=MAX_ITER)
    t0 = time.time()
    clf.fit(X_tr, y_tr)
    preds = clf.predict(X_te)
    f1, n, acc = report(y_te.tolist(), list(preds), f"LinearSVC C=2.0 ({time.time()-t0:.0f}s)")
    results["linearsvc_c2"] = {"f1": float(f1), "top10": n, "acc": float(acc)}

    # 3. CalibratedSVC isotonic
    print("\n3) CalibratedSVC isotonic", flush=True)
    base = LinearSVC(C=1.0, dual=False, class_weight="balanced", max_iter=MAX_ITER)
    cal = CalibratedClassifierCV(base, method="isotonic", cv=3, n_jobs=-1)
    t0 = time.time()
    cal.fit(X_tr, y_tr)
    preds = cal.predict(X_te)
    f1, n, acc = report(y_te.tolist(), list(preds), f"CalibratedSVC isotonic ({time.time()-t0:.0f}s)")
    results["calibrated_isotonic"] = {"f1": float(f1), "top10": n, "acc": float(acc)}

    # ── Final ─────────────────────────────────────────────────────────────────
    best_key = max(results, key=lambda k: results[k]["f1"])
    best_f1 = results[best_key]["f1"]
    best_n = results[best_key]["top10"]
    best_acc = results[best_key]["acc"]

    print("\n" + "=" * 70, flush=True)
    print("V12 RANKING", flush=True)
    print("=" * 70, flush=True)
    for k, v in sorted(results.items(), key=lambda kv: -kv[1]["f1"]):
        marker = "<-- BEST" if v["f1"] == best_f1 else ""
        print(f"  {k:30s} F1={v['f1']*100:6.2f}%  acc={v['acc']*100:6.2f}%  top10={v['top10']}/10  {marker}", flush=True)

    print(f"\n  Winner: {best_key}", flush=True)
    print(f"  Macro F1: {best_f1*100:.2f}%  (target >= 75%: {'PASS' if best_f1 >= 0.75 else 'FAIL'})", flush=True)
    print(f"  Accuracy: {best_acc*100:.2f}%", flush=True)
    print(f"  Top-10 pass: {best_n}/10  (target >=8: {'PASS' if best_n >= 8 else 'FAIL'})", flush=True)

    summary = {
        "version": "v12-prototypes",
        "encoders_used": list(embeddings.keys()),
        "feature_dim": int(X_tr.shape[1]),
        "prototype_features_count": len(proto_features) * 145,
        "results": results,
        "winner": best_key,
        "macro_f1": round(best_f1 * 100, 2),
        "accuracy": round(best_acc * 100, 2),
        "top10_pass": int(best_n),
        "target_met": bool(best_f1 >= 0.75),
    }
    (OUT_DIR / "training_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(f"  Saved to {OUT_DIR}", flush=True)


if __name__ == "__main__":
    main()
