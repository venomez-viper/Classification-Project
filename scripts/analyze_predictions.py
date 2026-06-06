"""Apply Option A (decidable-subset) and Option B (segment-share weighted) analyses
to a test_predictions.csv produced by any model trained against task1_test.csv.

Usage:
    python scripts/analyze_predictions.py <path_to_test_predictions.csv> [--name NAME]

The predictions CSV must have columns:
    true_code, pred_code
indexed in the same row order as llm_finetuning/data/task1_test.csv (10,717 rows).

Optionally accepts --probs <path> for a per-row top-k JSON file (Option B-strict).
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, classification_report

ROOT = Path(__file__).resolve().parent.parent
ENRICHED_TEST = ROOT / "llm_finetuning" / "data" / "task1_test_enriched.csv"


def macro_f1(y_true, y_pred) -> float:
    return f1_score(y_true, y_pred, average="macro", zero_division=0)


def report_subset(name: str, y_true, y_pred, n_classes_overall: int):
    """F1 on a subset, plus how many classes are present."""
    n = len(y_true)
    if n == 0:
        print(f"  {name:<35s} (empty subset)")
        return None
    f1 = macro_f1(y_true, y_pred)
    acc = (np.asarray(y_true) == np.asarray(y_pred)).mean()
    n_classes = len(set(y_true) | set(y_pred))
    coverage = n / 10717
    print(
        f"  {name:<35s} n={n:>5d} ({coverage:5.1%})  "
        f"acc={acc:6.2%}  macroF1={f1:6.2%}  classes_seen={n_classes}/{n_classes_overall}"
    )
    return {"name": name, "n": n, "coverage": coverage, "acc": acc, "macro_f1": f1}


def option_a_decidable(df: pd.DataFrame) -> dict:
    """Option A: macro F1 on the decidable subset."""
    print("\n=== OPTION A — Decidable-subset macro F1 ===")
    n_classes_overall = df["true_code"].nunique()

    results = []
    # Headline: full set
    results.append(
        report_subset("FULL SET (sanity)", df["true_code"], df["pred_code"], n_classes_overall)
    )

    # Subset 1: single-code companies only
    s = df[df["company_kind"] == "single_code"]
    results.append(
        report_subset(
            "Single-code companies only", s["true_code"], s["pred_code"], n_classes_overall
        )
    )

    # Subset 2: single-code + largest-segment of multi-code
    mask = (df["company_kind"] == "single_code") | (
        (df["company_kind"] == "multi_code")
        & (df["is_largest_share_segment"] == True)  # noqa: E712
    )
    s = df[mask]
    results.append(
        report_subset(
            "Single + largest-segment of multi",
            s["true_code"],
            s["pred_code"],
            n_classes_overall,
        )
    )

    # Subset 3: drop conglomerates (sector 310)
    s = df[~df["true_code"].astype(str).str.startswith("310")]
    results.append(
        report_subset(
            "Excluding sector-310 conglomerates",
            s["true_code"],
            s["pred_code"],
            n_classes_overall,
        )
    )

    # Subset 4: drop sector 310 AND require single-code
    mask = (df["company_kind"] == "single_code") & (
        ~df["true_code"].astype(str).str.startswith("310")
    )
    s = df[mask]
    results.append(
        report_subset(
            "Single-code AND not sector-310",
            s["true_code"],
            s["pred_code"],
            n_classes_overall,
        )
    )

    # Per company-kind breakdown
    print("\n  --- by company_kind ---")
    for kind in ("single_code", "multi_code", "unknown"):
        s = df[df["company_kind"] == kind]
        if len(s):
            f1 = macro_f1(s["true_code"], s["pred_code"])
            acc = (s["true_code"] == s["pred_code"]).mean()
            print(
                f"  {kind:<35s} n={len(s):>5d}  acc={acc:6.2%}  macroF1={f1:6.2%}"
            )

    print("\n  --- by codes-per-company bucket ---")
    for bucket, label in [(1, "1 code"), (2, "2 codes"), (3, "3 codes"), (None, "4+ codes")]:
        if bucket is None:
            s = df[df["n_codes_for_company"] >= 4]
        else:
            s = df[df["n_codes_for_company"] == bucket]
        if len(s):
            f1 = macro_f1(s["true_code"], s["pred_code"])
            acc = (s["true_code"] == s["pred_code"]).mean()
            print(
                f"  {label:<35s} n={len(s):>5d}  acc={acc:6.2%}  macroF1={f1:6.2%}"
            )

    return {"option_a": results}


def option_b_company_aggregated(df: pd.DataFrame) -> dict:
    """Option B: per-company aggregation by revenue_share.

    For each company, aggregate per-row predictions into a single 'company prediction'
    weighted by revenue_share. Then evaluate the company prediction against EACH segment's
    true label — the row is correct if the dominant company prediction equals its segment's
    true label.

    Note: a stronger Option B would require per-row top-k probabilities, not just argmax.
    This argmax-only version is a first cut.
    """
    print("\n=== OPTION B — Segment-share-weighted prediction (argmax-only) ===")
    n_classes_overall = df["true_code"].nunique()

    df = df.copy()
    df["revenue_share_clip"] = df["revenue_share"].clip(lower=0).fillna(0)

    # Per company, find the prediction with the highest sum of revenue_share
    def dominant_pred(group):
        if group["revenue_share_clip"].sum() == 0:
            # No share info: majority vote
            return group["pred_code"].mode().iloc[0]
        weighted = group.groupby("pred_code")["revenue_share_clip"].sum()
        return weighted.idxmax()

    has_co = df.dropna(subset=["CompanyId"])
    co_pred = has_co.groupby("CompanyId").apply(dominant_pred)

    # Apply company-level prediction to each row (every row of company X gets the same pred)
    df["pred_co"] = df["CompanyId"].map(co_pred)

    # Sanity: only score rows that got a co-level prediction
    s = df.dropna(subset=["pred_co"])
    print("  Scoring strategy: each row's true label vs its company's dominant prediction")
    report_subset(
        "Co-aggregated argmax (full)",
        s["true_code"],
        s["pred_co"],
        n_classes_overall,
    )

    # Same restricted to single-code (sanity — should match Option A single-code)
    s2 = s[s["company_kind"] == "single_code"]
    report_subset(
        "Co-aggregated, single-code only",
        s2["true_code"],
        s2["pred_co"],
        n_classes_overall,
    )

    # And a smarter scoring: a company prediction is "correct" if it equals ANY of its
    # true segment codes (i.e., we identified at least one real segment of the company)
    print("\n  --- Permissive scoring: pred is correct if it matches ANY segment of the company ---")
    company_true_codes = has_co.groupby("CompanyId")["true_code"].apply(set)
    has_co["matches_any"] = has_co.apply(
        lambda r: r["pred_code"] in company_true_codes.get(r["CompanyId"], set()),
        axis=1,
    )
    perm_acc = has_co["matches_any"].mean()
    print(f"  Permissive row accuracy: {perm_acc:6.2%}  (vs strict {((has_co['true_code']==has_co['pred_code']).mean()):.2%})")

    # By kind
    for kind in ("single_code", "multi_code"):
        sub = has_co[has_co["company_kind"] == kind]
        if len(sub):
            print(
                f"    {kind:<20s} permissive={sub['matches_any'].mean():6.2%}  strict={((sub['true_code']==sub['pred_code']).mean()):.2%}"
            )

    return {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("predictions_csv", type=str)
    ap.add_argument("--name", default=None, help="Friendly name for this run")
    args = ap.parse_args()

    pred_path = Path(args.predictions_csv)
    name = args.name or pred_path.stem

    print(f"Loading predictions: {pred_path}")
    preds = pd.read_csv(pred_path)
    if "true_code" not in preds.columns or "pred_code" not in preds.columns:
        raise SystemExit(
            f"predictions CSV must have columns true_code, pred_code; got {list(preds.columns)}"
        )

    print(f"Loading enriched test: {ENRICHED_TEST}")
    enriched = pd.read_csv(ENRICHED_TEST)

    if len(preds) != len(enriched):
        raise SystemExit(
            f"row-count mismatch: predictions={len(preds)}, enriched test={len(enriched)}"
        )

    df = enriched.copy()
    df["true_code"] = preds["true_code"].values
    df["pred_code"] = preds["pred_code"].values
    # Sanity: enriched mstar_code should match true_code
    if not (df["mstar_code"].astype(str) == df["true_code"].astype(str)).all():
        mismatches = (df["mstar_code"].astype(str) != df["true_code"].astype(str)).sum()
        print(f"  WARN: {mismatches} rows have mstar_code != true_code (different join order?)")

    print(f"\n### Analysis for: {name} ###")
    overall_f1 = macro_f1(df["true_code"], df["pred_code"])
    overall_acc = (df["true_code"] == df["pred_code"]).mean()
    print(f"Headline: macro F1 = {overall_f1:.4%}  acc = {overall_acc:.4%}")

    option_a_decidable(df)
    option_b_company_aggregated(df)


if __name__ == "__main__":
    main()
