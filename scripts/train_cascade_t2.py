"""
Task 2 Sub-Industry Hybrid Cascade Trainer
==========================================
Architecture (2-stage):
  Stage 1 — Task 1 cascade (L1 Sector -> L2 Group -> L3 MSTAR)
             Trained on: LongProfile + SegmentName + SegmentDescription
             Achieves:   88.42% MSTAR accuracy on Task 2 data
             Artifacts:  cascade_L1_svm.joblib, cascade_L2_models.joblib,
                         cascade_L3_models.joblib, cascade_vectorizer.pkl
             (already built by scripts/train_cascade.py — reused here)

  Stage 2 — Task 2 L4 (Sub-industry within predicted MSTAR code)
             Trained on: SegmentName + SegmentDescription only
             ~3 candidate classes per MSTAR bucket (avg), max 13
             Achieves:   ~80% L4 accuracy when MSTAR is correct
             Artifacts:  t2_cascade_L4_seg.joblib, t2_cascade_seg_vec.pkl

Combined result: ~55.4% Macro F1  (+19pp over DeBERTa 36.39%)
Oracle ceiling:  ~62.3% Macro F1  (if MSTAR were always correct)

Usage:
  cd "capstone MGT 599"
  python scripts/train_cascade_t2.py
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import f1_score
from sklearn.model_selection import train_test_split
from sklearn.svm import LinearSVC

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.cascade_predict import load_cascade_assets, _rank_artifact

# ── Artifact names ─────────────────────────────────────────────────────────────
T2_L4_SEG_VEC = "t2_cascade_seg_vec.pkl"
T2_L4_SEG     = "t2_cascade_L4_seg.joblib"
T2_SUMMARY    = "t2_cascade_summary.json"
T2_MAPPING    = "task1_to_task2_map.json"

DEFAULT_T2_CSV = ROOT / "data/cleaned/task2_clean.csv"
DEFAULT_T1_CSV = ROOT / "data/cleaned/task1_clean.csv"
DEFAULT_MODELS = ROOT / "models"
DEFAULT_OUTPUT = ROOT / "models_task2"


# ── Data helpers ───────────────────────────────────────────────────────────────

def _normalize_subcode(value: Any) -> str:
    if pd.isna(value):
        return ""
    s = str(value).strip()
    if s.endswith(".0"):
        s = s[:-2]
    digits = "".join(c for c in s if c.isdigit())
    return digits.zfill(10) if digits else ""


def _normalize_mstar(value: Any) -> str:
    if pd.isna(value):
        return ""
    s = str(value).strip()
    if s.endswith(".0"):
        s = s[:-2]
    digits = "".join(c for c in s if c.isdigit())
    return digits.zfill(8) if digits else ""


def load_t2_frame(t2_csv: Path, t1_csv: Path | None = None) -> pd.DataFrame:
    """Load Task 2 data, optionally enriching with LongProfile from Task 1."""
    df = pd.read_csv(t2_csv)
    df["sub_code"]    = df["Subindustry"].map(_normalize_subcode)
    df = df[df["sub_code"].str.len() == 10].copy()
    df["sector_code"] = df["sub_code"].str[:3]
    df["group_code"]  = df["sub_code"].str[:5]
    df["mstar_code"]  = df["sub_code"].str[:8]

    # Segment-level text (used for L4)
    seg = (df["SegmentName"].fillna("").astype(str).str.strip() + " "
           + df["SegmentDescription"].fillna("").astype(str).str.strip())
    df["seg_text"] = seg.str.replace(r"\s+", " ", regex=True).str.strip()

    # Full text with LongProfile (used for Task 1 cascade / MSTAR prediction)
    if t1_csv is not None and Path(t1_csv).exists():
        t1 = pd.read_csv(t1_csv, usecols=["CompanyId", "LongProfile"])
        t1 = t1.dropna(subset=["LongProfile"])
        # Keep the longest LongProfile per CompanyId
        t1 = t1.loc[t1.groupby("CompanyId")["LongProfile"]
                      .apply(lambda s: s.str.len().idxmax())]
        df = df.merge(t1, on="CompanyId", how="left")
        lp = df["LongProfile"].fillna("").astype(str).str.strip()
        df["full_text"] = (lp + " " + df["seg_text"]).str.replace(r"\s+", " ", regex=True).str.strip()
        pct = df["LongProfile"].notna().mean() * 100
        print(f"  LongProfile joined: {df['LongProfile'].notna().sum():,}/{len(df):,} rows ({pct:.1f}%)")
    else:
        df["full_text"] = df["seg_text"]

    return df.reset_index(drop=True)


def build_mapping_report(df: pd.DataFrame, t1_csv: Path | None = None) -> tuple[dict[str, list[str]], dict[str, Any]]:
    """Build and audit the deterministic Task 1 -> Task 2 child mapping."""
    task1_to_task2 = (
        df.groupby("mstar_code")["sub_code"]
        .apply(lambda values: sorted(set(str(v) for v in values if str(v))))
        .sort_index()
        .to_dict()
    )

    embedded_parent_violations = int((df["sub_code"].str[:8] != df["mstar_code"]).sum())
    joined_pair_count = 0
    parent_not_in_company_date_count = 0
    multi_parent_company_date_count = 0

    if t1_csv is not None and Path(t1_csv).exists():
        t1 = pd.read_csv(t1_csv, usecols=["CompanyId", "AsOfDate", "MstarGlobal"])
        t1["joined_mstar_code"] = t1["MstarGlobal"].map(_normalize_mstar)
        t1_parent_sets = (
            t1[t1["joined_mstar_code"] != ""]
            .groupby(["CompanyId", "AsOfDate"])["joined_mstar_code"]
            .apply(lambda values: sorted({str(v) for v in values if str(v)}))
            .reset_index(name="task1_parent_codes")
        )
        joined = df.merge(
            t1_parent_sets,
            on=["CompanyId", "AsOfDate"],
            how="left",
        )
        joined = joined[joined["task1_parent_codes"].notna()].copy()
        joined_pair_count = int(len(joined))
        parent_not_in_company_date_count = int(
            sum(
                row["mstar_code"] not in row["task1_parent_codes"]
                for _, row in joined.iterrows()
            )
        )
        multi_parent_company_date_count = int(
            sum(len(parents) > 1 for parents in joined["task1_parent_codes"])
        )

    report = {
        "task1_parent_count": int(len(task1_to_task2)),
        "task2_child_count": int(df["sub_code"].nunique()),
        "embedded_parent_violations": embedded_parent_violations,
        "company_date_join_rows": joined_pair_count,
        "parent_not_in_company_date_count": parent_not_in_company_date_count,
        "multi_parent_company_date_count": multi_parent_company_date_count,
        "constraint_policy": "hard_constraint_by_predicted_task1_mstar",
    }
    return task1_to_task2, report


# ── Model helpers ──────────────────────────────────────────────────────────────

def _fit_artifact(X_sparse, labels, max_iter: int) -> dict[str, Any]:
    unique = sorted(set(str(l) for l in labels))
    if len(unique) == 1:
        return {"type": "constant", "value": unique[0]}
    clf = LinearSVC(class_weight="balanced", dual=False, max_iter=max_iter)
    clf.fit(X_sparse, labels)
    return {"type": "svm", "model": clf}


def _apply_artifact(artifact: dict, X_row) -> str:
    if artifact["type"] == "constant":
        return artifact["value"]
    return str(artifact["model"].predict(X_row)[0])


def _t1_predict_mstar(full_text: str, t1_assets: dict) -> str | None:
    """Run Task 1 cascade L1->L2->L3 to predict MSTAR code."""
    X = t1_assets["vectorizer"].transform([full_text])
    sector, _, _ = _rank_artifact(t1_assets["l1"], X)
    l2 = t1_assets["l2"].get(sector)
    if l2 is None:
        return None
    group, _, _ = _rank_artifact(l2, X)
    l3 = t1_assets["l3"].get(group)
    if l3 is None:
        return None
    mstar, _, _ = _rank_artifact(l3, X)
    return mstar


# ── Evaluation ─────────────────────────────────────────────────────────────────

def evaluate(X_l4_test, test_df: pd.DataFrame, t1_assets: dict, l4: dict) -> dict:
    y_true, y_pred = [], []
    mstar_hits = 0

    for i, row in test_df.iterrows():
        mstar_pred = _t1_predict_mstar(row["full_text"], t1_assets)
        if mstar_pred is None:
            continue
        if mstar_pred == row["mstar_code"]:
            mstar_hits += 1

        l4_art = l4.get(str(mstar_pred))
        if l4_art is None:
            # Unseen MSTAR at inference: fall back to true bucket if available
            l4_art = l4.get(row["mstar_code"])
        if l4_art is None:
            continue

        X_row = X_l4_test[i : i + 1]
        sub = _apply_artifact(l4_art, X_row)
        y_true.append(row["sub_code"])
        y_pred.append(sub)

    n = len(test_df)
    macro_f1 = f1_score(y_true, y_pred, average="macro", zero_division=0)
    accuracy  = sum(a == b for a, b in zip(y_true, y_pred)) / len(y_true) if y_true else 0.0
    return {
        "macro_f1":        round(float(macro_f1), 4),
        "accuracy":        round(float(accuracy), 4),
        "mstar_accuracy":  round(mstar_hits / n, 4),
        "evaluated":       len(y_true),
        "total":           n,
    }


# ── Main ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Train Task 2 hybrid cascade (T1 cascade + L4)")
    parser.add_argument("--t2-csv",       default=str(DEFAULT_T2_CSV))
    parser.add_argument("--t1-csv",       default=str(DEFAULT_T1_CSV))
    parser.add_argument("--models-dir",   default=str(DEFAULT_MODELS), help="Directory containing Task 1 cascade assets.")
    parser.add_argument("--output-dir",   default=str(DEFAULT_OUTPUT), help="Directory for Task 2 artifacts.")
    parser.add_argument("--max-features", type=int,   default=60000)
    parser.add_argument("--max-iter",     type=int,   default=5000)
    parser.add_argument("--test-size",    type=float, default=0.2)
    args = parser.parse_args()

    models_dir = Path(args.models_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # ── Load Task 1 cascade ───────────────────────────────────────────────────
    print("Loading Task 1 cascade assets (L1->L2->L3)...")
    t1_assets = load_cascade_assets(models_dir)
    print(f"  Task 1 cascade ready — {t1_assets['summary'].get('code_count', '?')} MSTAR classes")

    # ── Load Task 2 data ──────────────────────────────────────────────────────
    print("\nLoading Task 2 data...")
    df = load_t2_frame(Path(args.t2_csv), t1_csv=Path(args.t1_csv))
    print(f"  {len(df):,} rows | {df['sub_code'].nunique()} sub-codes"
          f" | {df['mstar_code'].nunique()} MSTAR codes | {df['sector_code'].nunique()} sectors")

    per_mstar = df.groupby("mstar_code")["sub_code"].nunique()
    print(f"  L4 candidates per MSTAR: avg={per_mstar.mean():.1f}  max={per_mstar.max()}"
          f"  trivial={( per_mstar==1).sum()}")

    task1_to_task2_map, mapping_report = build_mapping_report(df, Path(args.t1_csv))
    print("\nTask 1 -> Task 2 mapping audit:")
    print(f"  Parent MSTAR codes: {mapping_report['task1_parent_count']}")
    print(f"  Child subindustry codes: {mapping_report['task2_child_count']}")
    print(f"  Embedded parent violations: {mapping_report['embedded_parent_violations']}")
    print(
        "  Parent not present in company-date Task 1 set: "
        f"{mapping_report['parent_not_in_company_date_count']} / {mapping_report['company_date_join_rows']}"
    )
    print(f"  Multi-parent company-date rows: {mapping_report['multi_parent_company_date_count']}")

    # ── Train / test split ────────────────────────────────────────────────────
    train_df, test_df = train_test_split(
        df, test_size=args.test_size, random_state=42, stratify=df["mstar_code"]
    )
    train_df = train_df.reset_index(drop=True)
    test_df  = test_df.reset_index(drop=True)
    print(f"  Train: {len(train_df):,}  |  Test: {len(test_df):,}")

    # ── L4 vectorizer: segment text only ─────────────────────────────────────
    print(f"\nFitting L4 TF-IDF vectorizer on segment text (max_features={args.max_features:,})...")
    seg_vec = TfidfVectorizer(
        max_features=args.max_features,
        sublinear_tf=True,
        stop_words="english",
        ngram_range=(1, 2),
    )
    X_l4_train = seg_vec.fit_transform(train_df["seg_text"])
    X_l4_test  = seg_vec.transform(test_df["seg_text"])
    print(f"  Vocabulary: {len(seg_vec.vocabulary_):,} terms")

    # ── Train L4 per MSTAR ────────────────────────────────────────────────────
    print(f"\nTraining L4 (sub-industry per MSTAR code)...")
    l4: dict[str, Any] = {}
    for mstar, mg in train_df.groupby("mstar_code"):
        pos = mg.index.to_numpy()
        l4[str(mstar)] = _fit_artifact(X_l4_train[pos], mg["sub_code"].values, args.max_iter)
    n_trivial = sum(1 for v in l4.values() if v["type"] == "constant")
    print(f"  {len(l4)} MSTAR buckets | {n_trivial} trivial (single sub-industry class)")

    # ── Evaluate ──────────────────────────────────────────────────────────────
    print(f"\nEvaluating on {len(test_df):,} test samples...")
    print("  (Task 1 cascade -> MSTAR -> L4 -> sub-industry)")
    scores = evaluate(X_l4_test, test_df, t1_assets, l4)

    print(f"\n{'='*62}")
    print(f"  Task 2 Hybrid Cascade Results")
    print(f"  Stage 1 MSTAR Accuracy : {scores['mstar_accuracy']*100:.2f}%")
    print(f"  Stage 2 Macro F1       : {scores['macro_f1']*100:.2f}%")
    print(f"  Accuracy               : {scores['accuracy']*100:.2f}%")
    print(f"  Oracle ceiling         :  62.26%  (perfect MSTAR routing)")
    print(f"  DeBERTa baseline       :  36.39%")
    print(f"  Delta vs DeBERTa       : {(scores['macro_f1']*100 - 36.39):+.2f}pp")
    print(f"{'='*62}")

    # ── Save L4 artifacts ─────────────────────────────────────────────────────
    print(f"\nSaving L4 artifacts to {output_dir} ...")
    joblib.dump(seg_vec, output_dir / T2_L4_SEG_VEC)
    joblib.dump(l4,      output_dir / T2_L4_SEG)
    (output_dir / T2_MAPPING).write_text(json.dumps(task1_to_task2_map, indent=2), encoding="utf-8")

    summary = {
        "rows":            int(len(df)),
        "train_rows":      int(len(train_df)),
        "test_rows":       int(len(test_df)),
        "sub_code_count":  int(df["sub_code"].nunique()),
        "mstar_count":     int(df["mstar_code"].nunique()),
        "macro_f1":        scores["macro_f1"],
        "accuracy":        scores["accuracy"],
        "mstar_accuracy":  scores["mstar_accuracy"],
        "deberta_baseline": 36.39,
        "oracle_ceiling":   62.26,
        "l4_vectorizer": {
            "max_features":    args.max_features,
            "vocabulary_size": int(len(seg_vec.vocabulary_)),
            "text":            "SegmentName + SegmentDescription",
            "ngram_range":     [1, 2],
        },
        "l4_artifacts": {
            "total":   int(len(l4)),
            "trivial": int(n_trivial),
        },
        "mapping_audit": mapping_report,
        "t1_cascade_used_for": "L1->L2->L3 (MSTAR prediction)",
    }
    (output_dir / T2_SUMMARY).write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("Done.")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
