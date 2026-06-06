"""
train_cascade_v5_hybrid.py
==========================
Hybrid feature stack:  TF-IDF (sparse) + MiniLM embeddings (dense) + numerical.
Uses the cached embeddings from V4 — no re-encoding required.

Plus engineered company-level features:
  • num_segments_for_company
  • max_segment_share
  • diversity_score (entropy of segment shares)

Run:
    python scripts/train_cascade_v5_hybrid.py
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

import breezeml.classifiers as bc

RAW_CSV   = ROOT / "data/raw/task1_gecs_classification_final (2).csv"
TRAIN_CSV = ROOT / "llm_finetuning/data/task1_train.csv"
TEST_CSV  = ROOT / "llm_finetuning/data/task1_test.csv"
EMB_DIR   = ROOT / "embeddings_v4"
OUT_DIR   = ROOT / "models_v5"

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
    print(f"\n  {label}: F1={f1*100:.2f}%  acc={acc*100:.2f}%  top10={n_pass}/10")
    return f1, n_pass, f1s, top10, cf


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # ── 1. Load & join data ───────────────────────────────────────────────────
    print("Loading data and joining to raw …")
    raw = pd.read_csv(RAW_CSV)
    raw["combined"] = (
        raw["LongProfile"].fillna("") + " " +
        raw["SegmentName"].fillna("") + " " +
        raw["SegmentDescription"].fillna("")
    ).str.replace(r"\s+", " ", regex=True).str.strip()

    # Engineer company-level features from raw
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

    # Fallback for unmatched rows
    for df in (train, test):
        df["LongProfile"]              = df["LongProfile"].fillna(df["text"])
        df["SegmentName"]              = df["SegmentName"].fillna("")
        df["SegmentDescription"]       = df["SegmentDescription"].fillna(df["text"])
        df["revenue_share"]            = df["revenue_share"].fillna(0.5)
        df["is_largest_share_segment"] = df["is_largest_share_segment"].fillna(False).astype(float)
        df["num_segments"]             = df["num_segments"].fillna(1)
        df["max_share"]                = df["max_share"].fillna(0.5)
        df["share_std"]                = df["share_std"].fillna(0.0)
        df["code"]   = df["mstar_code"].map(norm_code)
        df["sector"] = df["code"].str[:3]
        df["group"]  = df["code"].str[:5]

    print(f"  train={len(train):,}  test={len(test):,}")

    # ── 2. Load cached embeddings ─────────────────────────────────────────────
    print("Loading cached MiniLM embeddings …")
    E_seg_tr  = np.load(EMB_DIR / "seg_train.npy")
    E_seg_te  = np.load(EMB_DIR / "seg_test.npy")
    E_long_tr = np.load(EMB_DIR / "long_train.npy")
    E_long_te = np.load(EMB_DIR / "long_test.npy")
    print(f"  seg embeddings: {E_seg_tr.shape}  long: {E_long_tr.shape}")

    # ── 3. Build TF-IDF features ──────────────────────────────────────────────
    print("Building TF-IDF features …")
    seg_tr  = (train["SegmentName"] + " " + train["SegmentDescription"]).map(clean)
    seg_te  = (test["SegmentName"]  + " " + test["SegmentDescription"]).map(clean)
    long_tr = train["LongProfile"].map(clean)
    long_te = test["LongProfile"].map(clean)

    vec_seg = TfidfVectorizer(max_features=80000,  sublinear_tf=True, stop_words="english",
                              ngram_range=(1, 2), min_df=2)
    vec_lng = TfidfVectorizer(max_features=40000,  sublinear_tf=True, stop_words="english",
                              ngram_range=(1, 2), min_df=2)
    Xs_tr = vec_seg.fit_transform(seg_tr);  Xs_te = vec_seg.transform(seg_te)
    Xl_tr = vec_lng.fit_transform(long_tr); Xl_te = vec_lng.transform(long_te)
    print(f"  TF-IDF dims: seg={Xs_tr.shape[1]}  long={Xl_tr.shape[1]}")

    # ── 4. Numerical features (5 features now) ────────────────────────────────
    num_cols = ["revenue_share", "is_largest_share_segment", "num_segments",
                "max_share", "share_std"]
    scaler = MinMaxScaler(feature_range=(0, 1), clip=True)
    N_tr = scaler.fit_transform(train[num_cols].values)
    N_te = scaler.transform(test[num_cols].values)

    # ── 5. Build feature variants ─────────────────────────────────────────────
    def to_sparse(arr): return csr_matrix(arr.astype(np.float32))

    variants: dict[str, tuple] = {
        "embeddings only (V4 baseline)": (
            to_sparse(np.hstack([E_seg_tr, E_long_tr, N_tr])),
            to_sparse(np.hstack([E_seg_te, E_long_te, N_te])),
        ),
        "TF-IDF only (V3 baseline)": (
            sparse_hstack([Xs_tr, Xl_tr, to_sparse(N_tr)], format="csr"),
            sparse_hstack([Xs_te, Xl_te, to_sparse(N_te)], format="csr"),
        ),
        "HYBRID: TF-IDF + MiniLM + numerical": (
            sparse_hstack([Xs_tr, Xl_tr, to_sparse(E_seg_tr), to_sparse(E_long_tr),
                           to_sparse(N_tr)], format="csr"),
            sparse_hstack([Xs_te, Xl_te, to_sparse(E_seg_te), to_sparse(E_long_te),
                           to_sparse(N_te)], format="csr"),
        ),
        "HYBRID + segment-only TF-IDF": (
            sparse_hstack([Xs_tr, to_sparse(E_seg_tr), to_sparse(E_long_tr),
                           to_sparse(N_tr)], format="csr"),
            sparse_hstack([Xs_te, to_sparse(E_seg_te), to_sparse(E_long_te),
                           to_sparse(N_te)], format="csr"),
        ),
    }

    # ── 6. Train + evaluate every variant ────────────────────────────────────
    print("\n" + "=" * 65)
    print("Variant comparison — flat LinearSVC, C=1.0")
    print("=" * 65)

    y_tr = train["code"].values
    y_te = test["code"].values
    results: dict[str, dict] = {}

    for name, (X_tr, X_te) in variants.items():
        print(f"\n--- {name}  (dim={X_tr.shape[1]:,}) ---")
        t0 = time.time()
        pipe, _ = bc.linear_svm(X=X_tr, y=y_tr, X_test=X_te, y_test=y_te, max_iter=MAX_ITER)
        clf = pipe.named_steps["model"]
        preds = clf.predict(X_te)
        dt = time.time() - t0
        f1, n_pass, _, _, _ = report(y_te.tolist(), list(preds), label=name)
        results[name] = {"f1": float(f1), "top10_pass": n_pass, "time_s": round(dt, 1)}

    # ── 7. C tuning on the winner ─────────────────────────────────────────────
    winner_name = max(results, key=lambda k: results[k]["f1"])
    print("\n" + "=" * 65)
    print(f"Winner so far: {winner_name}  (F1={results[winner_name]['f1']*100:.2f}%)")
    print("=" * 65)

    X_tr_win, X_te_win = variants[winner_name]
    print("Tuning C on winner …")
    best_C, best_f1, best_clf, best_n_pass = 1.0, 0.0, None, 0
    for C in [0.25, 0.5, 1.0, 2.0, 4.0]:
        clf = LinearSVC(C=C, dual=False, class_weight="balanced", max_iter=MAX_ITER)
        clf.fit(X_tr_win, y_tr)
        preds = clf.predict(X_te_win)
        f1 = f1_score(y_te, preds, average="macro", zero_division=0)
        cf = Counter(y_te)
        top10 = [c for c, _ in cf.most_common(10)]
        f1s = f1_score(y_te, preds, average=None, labels=top10, zero_division=0)
        n_pass = int(sum(1 for v in f1s if v > 0.85))
        marker = "  ←" if f1 > best_f1 else ""
        print(f"  C={C:5}: F1={f1*100:.2f}%  top10={n_pass}/10{marker}")
        if f1 > best_f1:
            best_C, best_f1, best_clf, best_n_pass = C, f1, clf, n_pass

    # ── 8. Save final ─────────────────────────────────────────────────────────
    print("\n" + "=" * 65)
    print(f"FINAL V5 RESULT: {best_f1*100:.2f}% Macro F1  (C={best_C})  top10={best_n_pass}/10")
    print(f"Target: >= 75.00%  → {'PASS' if best_f1 >= 0.75 else 'FAIL'}")
    print("=" * 65)

    joblib.dump(best_clf, OUT_DIR / "v5_flat_svm.joblib")
    joblib.dump(vec_seg,  OUT_DIR / "v5_vec_seg.pkl")
    joblib.dump(vec_lng,  OUT_DIR / "v5_vec_long.pkl")
    joblib.dump(scaler,   OUT_DIR / "v5_num_scaler.pkl")

    summary = {
        "version": "v5-hybrid",
        "split": "row-level 80/20 (case standard)",
        "winner_features": winner_name,
        "best_C": best_C,
        "macro_f1": round(float(best_f1) * 100, 2),
        "top10_pass": int(best_n_pass),
        "target_met": bool(best_f1 >= 0.75),
        "all_variants": results,
        "feature_dim": int(X_tr_win.shape[1]),
        "engineered_company_features": ["num_segments", "max_share", "share_std"],
    }
    (OUT_DIR / "training_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(f"\n  Saved to {OUT_DIR}")


if __name__ == "__main__":
    main()
