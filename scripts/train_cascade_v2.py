"""
train_cascade_v2.py — Improved Task 1 cascade with 4 targeted fixes:

  1. Honest split  — CompanyId-level 80/20 so no company leaks across train/test
  2. Dual vectorizers — LongProfile (100k TF-IDF) for L1/L2, segment text (50k) for L3
  3. Boilerplate stripping — remove "The company/Company" noise added by Morningstar anonymization
  4. Numerical features — revenue_share + is_largest_share_segment appended to each level
  5. BreezeML — uses breezeml.classifiers.linear_svm() (inner LinearSVC extracted for cascade)

Run:
    python scripts/train_cascade_v2.py

Saves artifacts to models_v2/ and prints a full honest evaluation report.
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
from scipy.sparse import csr_matrix, hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import f1_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import breezeml.classifiers as bc

RAW_CSV  = ROOT / "data/raw/task1_gecs_classification_final (2).csv"
OUT_DIR  = ROOT / "models_v2"

MAX_FEATURES_LONG = 50_000   # LongProfile vocab
MAX_FEATURES_SEG  = 100_000  # Segment vocab — wins the feature experiment
NGRAM             = (1, 2)
MIN_DF            = 2
MAX_ITER          = 5_000


# ── Text cleaning ─────────────────────────────────────────────────────────────

_BOILERPLATE = re.compile(
    r"\bThe [Cc]ompan(?:y|ies)\b"
    r"|\bcompany's\b"
    r"|\bsegment includes\b"
    r"|\bsegment comprises\b"
    r"|\bsegment engages in\b"
    r"|\boperating segment\b",
    re.IGNORECASE,
)

def clean(text: str) -> str:
    text = _BOILERPLATE.sub(" ", str(text))
    return re.sub(r"\s{2,}", " ", text).strip()


# ── Code normalisation ────────────────────────────────────────────────────────

def norm(v: Any) -> str:
    s = str(int(v))
    return s.zfill(8)


# ── Softmax helper (for inference) ───────────────────────────────────────────

def _softmax(a: np.ndarray) -> np.ndarray:
    a = np.asarray(a, dtype=np.float64)
    a -= a.max()
    e = np.exp(a)
    return e / e.sum()


# ── Fit one cascade artifact via BreezeML ────────────────────────────────────

def fit_artifact(X_train, y_train, X_test, y_test) -> tuple[dict, dict]:
    unique = sorted(set(str(v) for v in y_train))
    if len(unique) == 1:
        # Constant — only one possible label in this branch
        return {"type": "constant", "value": unique[0]}, {}

    pipe, report = bc.linear_svm(
        X=X_train, y=y_train,
        X_test=X_test, y_test=y_test,
        max_iter=MAX_ITER,
    )
    inner = pipe.named_steps["model"]          # extract LinearSVC from Pipeline
    return {"type": "svm", "model": inner}, report


# ── Predict one artifact (used for eval loop) ─────────────────────────────────

def predict_artifact(artifact: dict, Xi) -> tuple[str, float]:
    if artifact["type"] == "constant":
        return str(artifact["value"]), 100.0
    model = artifact["model"]
    scores = model.decision_function(Xi)
    classes = np.asarray(model.classes_, dtype=str)
    margins = np.asarray(scores[0], dtype=np.float64) if np.ndim(scores) > 1 else \
              np.array([-scores[0], scores[0]], dtype=np.float64)
    probs = _softmax(margins)
    best = int(np.argmax(probs))
    return str(classes[best]), round(float(probs[best]) * 100, 1)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # ── 1. Load raw data ──────────────────────────────────────────────────────
    print("Loading raw data …")
    raw = pd.read_csv(RAW_CSV)
    raw["code"]        = raw["MstarGlobal"].map(norm)
    raw["sector_code"] = raw["code"].str[:3]
    raw["group_code"]  = raw["code"].str[:5]
    print(f"  {len(raw):,} rows · {raw['code'].nunique()} classes · {raw['CompanyId'].nunique():,} companies")

    # ── 2. CompanyId-level 80/20 stratified split ─────────────────────────────
    print("\nBuilding CompanyId-level 80/20 split …")
    company_labels = (
        raw.groupby("CompanyId")["code"]
        .agg(lambda s: s.mode().iloc[0])   # one label per company
        .reset_index()
    )
    train_ids, test_ids = train_test_split(
        company_labels["CompanyId"],
        test_size=0.2,
        random_state=42,
        stratify=company_labels["code"],
    )
    train_df = raw[raw["CompanyId"].isin(train_ids)].copy().reset_index(drop=True)
    test_df  = raw[raw["CompanyId"].isin(test_ids)].copy().reset_index(drop=True)
    print(f"  Train: {len(train_df):,} rows · {train_df['CompanyId'].nunique():,} companies")
    print(f"  Test:  {len(test_df):,} rows  · {test_df['CompanyId'].nunique():,} companies")
    print(f"  Company overlap: {len(set(train_ids) & set(test_ids))} (must be 0)")

    # ── 3. Text cleaning + feature construction ───────────────────────────────
    print("\nBuilding text features …")

    long_tr = train_df["LongProfile"].fillna("").map(clean)
    long_te = test_df["LongProfile"].fillna("").map(clean)

    seg_tr = (
        train_df["SegmentName"].fillna("") + " " +
        train_df["SegmentDescription"].fillna("")
    ).map(clean)
    seg_te = (
        test_df["SegmentName"].fillna("") + " " +
        test_df["SegmentDescription"].fillna("")
    ).map(clean)

    # ── 4. Vectorize ──────────────────────────────────────────────────────────
    vec_long = TfidfVectorizer(
        max_features=MAX_FEATURES_LONG,
        sublinear_tf=True, stop_words="english",
        ngram_range=NGRAM, min_df=MIN_DF,
    )
    vec_seg = TfidfVectorizer(
        max_features=MAX_FEATURES_SEG,
        sublinear_tf=True, stop_words="english",
        ngram_range=NGRAM, min_df=MIN_DF,
    )

    X_long_tr = vec_long.fit_transform(long_tr)
    X_long_te = vec_long.transform(long_te)
    X_seg_tr  = vec_seg.fit_transform(seg_tr)
    X_seg_te  = vec_seg.transform(seg_te)
    print(f"  vec_long vocab: {len(vec_long.vocabulary_):,}  vec_seg vocab: {len(vec_seg.vocabulary_):,}")

    # ── 5. Numerical features (revenue_share + is_largest) ───────────────────
    scaler = MinMaxScaler(feature_range=(0, 1), clip=True)
    num_tr_raw = train_df[["revenue_share", "is_largest_share_segment"]].copy()
    num_te_raw = test_df[["revenue_share", "is_largest_share_segment"]].copy()
    num_tr_raw["is_largest_share_segment"] = num_tr_raw["is_largest_share_segment"].astype(float)
    num_te_raw["is_largest_share_segment"] = num_te_raw["is_largest_share_segment"].astype(float)

    num_tr = csr_matrix(scaler.fit_transform(num_tr_raw.values))
    num_te = csr_matrix(scaler.transform(num_te_raw.values))

    # ── Combined feature matrices ─────────────────────────────────────────────
    # All levels use BOTH seg + long vectorizers + numerical features.
    # Experiment showed stacking both beats either alone by ~2-16pp.
    X_both_tr = hstack([X_seg_tr, X_long_tr, num_tr], format="csr")
    X_both_te = hstack([X_seg_te, X_long_te, num_te], format="csr")
    # Aliases so rest of code is unchanged
    X_l12_tr = X_both_tr;  X_l12_te = X_both_te
    X_l3_tr  = X_both_tr;  X_l3_te  = X_both_te

    print(f"  All-level feature dim: {X_both_tr.shape[1]:,}")

    # ── 6. Train L1 (sector) ──────────────────────────────────────────────────
    print("\nTraining L1 (sector) via BreezeML …")
    l1_artifact, l1_report = fit_artifact(
        X_l12_tr, train_df["sector_code"],
        X_l12_te, test_df["sector_code"],
    )
    print(f"  L1 macro F1 on test: {l1_report.get('macro_f1', 'N/A')}")

    # ── 7. Train L2 (group per sector) ────────────────────────────────────────
    print("Training L2 (group per sector) …")
    l2_artifacts: dict[str, Any] = {}
    for sector, grp in train_df.groupby("sector_code", sort=True):
        tr_idx = grp.index
        te_grp = test_df[test_df["sector_code"] == sector]
        te_idx = te_grp.index
        art, _ = fit_artifact(
            X_l12_tr[tr_idx], grp["group_code"],
            X_l12_te[te_idx] if len(te_idx) else X_l12_te[:1],
            te_grp["group_code"] if len(te_idx) else grp["group_code"].iloc[:1],
        )
        l2_artifacts[str(sector)] = art
    n_const_l2 = sum(1 for a in l2_artifacts.values() if a["type"] == "constant")
    print(f"  {len(l2_artifacts)} L2 models · {n_const_l2} constants")

    # ── 8. Train L3 (code per group) ──────────────────────────────────────────
    print("Training L3 (code per group) …")
    l3_artifacts: dict[str, Any] = {}
    for group, grp in train_df.groupby("group_code", sort=True):
        tr_idx = grp.index
        te_grp = test_df[test_df["group_code"] == group]
        te_idx = te_grp.index
        art, _ = fit_artifact(
            X_l3_tr[tr_idx], grp["code"],
            X_l3_te[te_idx] if len(te_idx) else X_l3_te[:1],
            te_grp["code"] if len(te_idx) else grp["code"].iloc[:1],
        )
        l3_artifacts[str(group)] = art
    n_const_l3 = sum(1 for a in l3_artifacts.values() if a["type"] == "constant")
    print(f"  {len(l3_artifacts)} L3 models · {n_const_l3} constants")

    # ── 9. Full cascade evaluation on test set ────────────────────────────────
    print("\nEvaluating full cascade on test set …")
    preds, sector_preds, group_preds = [], [], []
    n = X_l12_te.shape[0]

    for i in range(n):
        Xi_l12 = X_l12_te[i]
        Xi_l3  = X_l3_te[i]

        sector, _ = predict_artifact(l1_artifact, Xi_l12)
        l2 = l2_artifacts.get(sector)
        if l2 is None:
            sector = train_df["sector_code"].value_counts().idxmax()
            l2 = l2_artifacts[sector]
        group, _ = predict_artifact(l2, Xi_l12)

        l3 = l3_artifacts.get(group)
        if l3 is None:
            group = (train_df[train_df["sector_code"] == sector]["group_code"]
                     .value_counts().idxmax())
            l3 = l3_artifacts[group]
        code, _ = predict_artifact(l3, Xi_l3)

        sector_preds.append(sector)
        group_preds.append(group)
        preds.append(code)

        if (i + 1) % 2000 == 0:
            print(f"  {i+1:,}/{n:,} …")

    true_codes   = test_df["code"].tolist()
    true_sectors = test_df["sector_code"].tolist()
    true_groups  = test_df["group_code"].tolist()

    l1_acc   = sum(sp == st for sp, st in zip(sector_preds, true_sectors)) / len(true_sectors)
    l2_acc   = sum(gp == gt for gp, gt in zip(group_preds, true_groups))   / len(true_groups)
    macro_f1 = f1_score(true_codes, preds, average="macro", zero_division=0)

    # Top-10 F1
    code_freq   = Counter(true_codes)
    top10_codes = [c for c, _ in code_freq.most_common(10)]
    f1_top10    = f1_score(true_codes, preds, average=None, labels=top10_codes, zero_division=0)

    # Error propagation
    l1_err = sum(sp != st for sp, st in zip(sector_preds, true_sectors))
    l2_err = sum(
        gp != gt
        for sp, st, gp, gt in zip(sector_preds, true_sectors, group_preds, true_groups)
        if sp == st
    )
    l3_err = sum(
        p != t
        for sp, st, gp, gt, p, t in zip(
            sector_preds, true_sectors, group_preds, true_groups, preds, true_codes
        )
        if sp == st and gp == gt
    )

    total = len(true_codes)
    print()
    print("=" * 60)
    print("V3 CASCADE EVALUATION — CompanyId split · both vectorizers")
    print("=" * 60)
    print(f"  L1 Sector accuracy : {l1_acc * 100:.2f}%")
    print(f"  L2 Group  accuracy : {l2_acc * 100:.2f}%")
    print(f"  L3 Macro F1        : {macro_f1 * 100:.2f}%  (target >= 75%)")
    print()
    print("  Error propagation:")
    print(f"    L1 wrong         : {l1_err:,} ({l1_err/total*100:.1f}%)")
    print(f"    L2 wrong|L1 ok   : {l2_err:,} ({l2_err/total*100:.1f}%)")
    print(f"    L3 wrong|L2 ok   : {l3_err:,} ({l3_err/total*100:.1f}%)")
    print()
    print("  Top-10 class F1 (case criterion: > 85%):")
    n_pass = 0
    for code, f1v in zip(top10_codes, f1_top10):
        status = "PASS" if f1v > 0.85 else "FAIL"
        if f1v > 0.85:
            n_pass += 1
        print(f"    [{status}] {code}: {f1v*100:.1f}%  n={code_freq[code]}")
    print(f"  Top-10 pass rate: {n_pass}/10")

    # ── 10. Save artifacts ────────────────────────────────────────────────────
    print(f"\nSaving V2 artifacts to {OUT_DIR} …")
    joblib.dump(vec_long,      OUT_DIR / "cascade_vec_long.pkl")
    joblib.dump(vec_seg,       OUT_DIR / "cascade_vec_seg.pkl")
    joblib.dump(scaler,        OUT_DIR / "cascade_num_scaler.pkl")
    joblib.dump(l1_artifact,   OUT_DIR / "cascade_L1_svm.joblib")
    joblib.dump(l2_artifacts,  OUT_DIR / "cascade_L2_models.joblib")
    joblib.dump(l3_artifacts,  OUT_DIR / "cascade_L3_models.joblib")

    summary = {
        "version":        "v3",
        "trained_on":     "CompanyId-level 80/20 split, both seg+long vectorizers",
        "train_rows":     int(len(train_df)),
        "test_rows":      int(len(test_df)),
        "train_companies": int(train_df["CompanyId"].nunique()),
        "test_companies":  int(test_df["CompanyId"].nunique()),
        "sector_count":   int(train_df["sector_code"].nunique()),
        "group_count":    int(train_df["group_code"].nunique()),
        "code_count":     int(train_df["code"].nunique()),
        "macro_f1":       round(float(macro_f1) * 100, 2),
        "l1_accuracy":    round(float(l1_acc) * 100, 2),
        "l2_accuracy":    round(float(l2_acc) * 100, 2),
        "top10_pass":     int(n_pass),
        "features": {
            "vec_long_size":  len(vec_long.vocabulary_),
            "vec_seg_size":   len(vec_seg.vocabulary_),
            "numerical":      ["revenue_share", "is_largest_share_segment"],
            "boilerplate_stripped": True,
        },
    }
    (OUT_DIR / "cascade_training_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print("Done.")
    print(f"\nV2 Macro F1: {macro_f1*100:.2f}%  (honest, CompanyId split, no leakage)")


if __name__ == "__main__":
    main()
