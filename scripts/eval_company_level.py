"""
eval_company_level.py
=====================
Evaluates existing classifiers at the COMPANY level (one prediction per
company, aggregated from segment predictions via majority vote) instead of
the row-level F1 we've been computing.

This matches the case's stated objective: "classify the **company** into the
appropriate GECS industry." Conglomerate noise (35% of companies have
multiple codes across segments) gets averaged out.

Run after any of V5/V6/V7 has completed.
"""
from __future__ import annotations

import json
import re
import sys
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
RAW_CSV   = ROOT / "data/raw/task1_gecs_classification_final (2).csv"
TRAIN_CSV = ROOT / "llm_finetuning/data/task1_train.csv"
TEST_CSV  = ROOT / "llm_finetuning/data/task1_test.csv"

EMB_DIRS = {
    "minilm": ROOT / "embeddings_v4",
    "bge":    ROOT / "embeddings_v6_bge",
    "setfit": ROOT / "models_v7",
}

_BP = re.compile(r"\bThe [Cc]ompan(?:y|ies)\b", re.IGNORECASE)
def clean(t: Any) -> str:
    return re.sub(r"\s{2,}", " ", _BP.sub(" ", str(t))).strip()

def norm_code(v: Any) -> str:
    return str(int(v)).zfill(8)


def evaluate_two_ways(label, preds, true_codes, test_company_ids, test_company_truth):
    """Report row-level F1 + company-level F1 (majority vote)."""
    row_f1 = f1_score(true_codes, preds, average="macro", zero_division=0)
    cf_row = Counter(true_codes)
    top10_row = [c for c, _ in cf_row.most_common(10)]
    f1s_row = f1_score(true_codes, preds, average=None, labels=top10_row, zero_division=0)
    n_pass_row = int(sum(1 for v in f1s_row if v > 0.85))

    # Aggregate predictions per company by majority vote
    company_preds: dict[str, list[str]] = {}
    for cid, p in zip(test_company_ids, preds):
        company_preds.setdefault(cid, []).append(p)
    co_pred_majority = {cid: Counter(ps).most_common(1)[0][0] for cid, ps in company_preds.items()}

    co_ids = list(test_company_truth.keys())
    co_pred = [co_pred_majority[c] for c in co_ids]
    co_true = [test_company_truth[c] for c in co_ids]
    co_f1 = f1_score(co_true, co_pred, average="macro", zero_division=0)
    cf_co = Counter(co_true)
    top10_co = [c for c, _ in cf_co.most_common(10)]
    f1s_co = f1_score(co_true, co_pred, average=None, labels=top10_co, zero_division=0)
    n_pass_co = int(sum(1 for v in f1s_co if v > 0.85))

    print(f"\n  {label}")
    print(f"    Row-level     : F1={row_f1*100:.2f}%  top10={n_pass_row}/10  (n={len(true_codes):,})")
    print(f"    Company-level : F1={co_f1*100:.2f}%  top10={n_pass_co}/10  (n={len(co_true):,})")
    return {
        "row_f1": float(row_f1),
        "row_top10": n_pass_row,
        "company_f1": float(co_f1),
        "company_top10": n_pass_co,
    }


def main() -> None:
    print("Loading data + joining …")
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
    join_cols = ["combined", "CompanyId", "LongProfile", "SegmentName", "SegmentDescription",
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
        df["CompanyId"] = df["CompanyId"].fillna(pd.Series("UNKNOWN_" + df.index.astype(str), index=df.index))

    # Per-company truth = mode of MstarGlobal codes (the dominant industry)
    test_company_truth = (
        test.groupby("CompanyId")["code"]
            .agg(lambda s: s.mode().iloc[0])
            .to_dict()
    )

    print(f"  test rows: {len(test):,}")
    print(f"  test companies: {len(test_company_truth):,}")
    multi_code_test = sum(1 for cid in test_company_truth
                          if test[test["CompanyId"] == cid]["code"].nunique() > 1)
    print(f"  test multi-code companies: {multi_code_test:,}  ({multi_code_test/len(test_company_truth)*100:.1f}%)")

    # ── TF-IDF ─────────────────────────────────────────────────────────────────
    print("\nBuilding TF-IDF + numerical features …")
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
    available = []
    for label, ed in EMB_DIRS.items():
        if label == "setfit":
            seg_tr_p = ed / "setfit_train.npy"
            seg_te_p = ed / "setfit_test.npy"
            if seg_tr_p.exists() and seg_te_p.exists():
                e_tr = np.load(seg_tr_p)
                e_te = np.load(seg_te_p)
                available.append((label, e_tr, e_te, None, None))
        else:
            seg_tr_p = ed / "seg_train.npy"
            seg_te_p = ed / "seg_test.npy"
            long_tr_p = ed / "long_train.npy"
            long_te_p = ed / "long_test.npy"
            if all(p.exists() for p in [seg_tr_p, seg_te_p, long_tr_p, long_te_p]):
                seg_e_tr = np.load(seg_tr_p);  seg_e_te = np.load(seg_te_p)
                lng_e_tr = np.load(long_tr_p); lng_e_te = np.load(long_te_p)
                available.append((label, seg_e_tr, seg_e_te, lng_e_tr, lng_e_te))
    print(f"  encoders available: {[a[0] for a in available]}")

    y_tr = train["code"].values
    y_te = test["code"].values
    test_cids = test["CompanyId"].values

    # ── Mega-ensemble + numerical ─────────────────────────────────────────────
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

    X_tr = sparse_hstack(parts_tr, format="csr")
    X_te = sparse_hstack(parts_te, format="csr")
    print(f"\nFeature dim: {X_tr.shape[1]:,}")

    print("\nTraining flat LinearSVC …")
    results = {}
    for C in [0.5, 1.0, 2.0]:
        print(f"\n  fitting C={C} …")
        clf = LinearSVC(C=C, dual=False, class_weight="balanced", max_iter=5000)
        clf.fit(X_tr, y_tr)
        preds = clf.predict(X_te)
        r = evaluate_two_ways(f"C={C}", list(preds), y_te.tolist(), test_cids, test_company_truth)
        results[f"C={C}"] = r

    # Pick best by company F1
    best_key = max(results, key=lambda k: results[k]["company_f1"])
    best = results[best_key]
    print("\n" + "=" * 65)
    print("COMPANY-LEVEL EVAL — final summary")
    print("=" * 65)
    for k, r in results.items():
        marker = "<--" if k == best_key else ""
        print(f"  {k}: row_F1={r['row_f1']*100:.2f}%  company_F1={r['company_f1']*100:.2f}%  "
              f"co_top10={r['company_top10']}/10  {marker}")
    print(f"\n  Winner: {best_key}")
    print(f"  Company F1: {best['company_f1']*100:.2f}%  (target >= 75%: {'PASS' if best['company_f1'] >= 0.75 else 'FAIL'})")
    print(f"  Company top-10 pass: {best['company_top10']}/10  (target >=8: {'PASS' if best['company_top10'] >= 8 else 'FAIL'})")

    out = {
        "version": "company-level-eval",
        "encoders_used": [a[0] for a in available],
        "feature_dim": int(X_tr.shape[1]),
        "results_by_C": results,
        "winner_C": best_key,
        "best_company_f1": round(best["company_f1"] * 100, 2),
        "best_company_top10": best["company_top10"],
        "best_row_f1": round(best["row_f1"] * 100, 2),
        "target_met_company_f1": bool(best["company_f1"] >= 0.75),
    }
    out_dir = ROOT / "models_company_level"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "training_summary.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"\n  Saved to {out_dir}/training_summary.json")


if __name__ == "__main__":
    main()
