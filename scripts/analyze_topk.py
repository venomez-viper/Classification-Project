"""Option B (smart) — analysis using top-k probabilities.

Reads test_predictions_topk.csv (true, top1..top5 codes + probs) and the enriched
test data (CompanyId, n_codes_for_company, revenue_share). Reports:

  1. Top-1 / Top-3 / Top-5 accuracy and macro F1
  2. Company-level "permissive": row correct if true_code is in the union of top-3
     codes across all rows of its company
  3. Revenue-share weighted company prediction: each company gets ONE prediction
     by summing per-row top-5 probs weighted by revenue_share; then row is correct
     if its true_code matches that company prediction
  4. Smart per-row reranking: for each row in a multi-code company, look up the
     OTHER segment codes the company actually has. If model's top-3 is split
     across segments, pick the candidate that matches a real company segment.
"""
import argparse
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score

ROOT = Path(__file__).resolve().parent.parent
ENRICHED = ROOT / "llm_finetuning" / "data" / "task1_test_enriched.csv"


def macro_f1(y_true, y_pred) -> float:
    y_true = pd.Series(y_true).astype(str).values
    y_pred = pd.Series(y_pred).astype(str).values
    return f1_score(y_true, y_pred, average="macro", zero_division=0)


def topk_accuracy(true_codes, topk_codes_array):
    """For each row, was the true code in any of the top-k predictions?"""
    hits = np.zeros(len(true_codes), dtype=bool)
    for i, t in enumerate(true_codes):
        hits[i] = t in topk_codes_array[i]
    return hits.mean()


def company_union_topk(df, k=3):
    """For each company, build the union of its rows' top-k predictions.
    Then a row is 'correct' if its true_code is in that union.
    """
    co_to_codes = defaultdict(set)
    topk_cols = [f"top{i}_code" for i in range(1, k + 1)]
    for _, r in df.iterrows():
        cid = r["CompanyId"]
        if pd.isna(cid):
            continue
        for c in topk_cols:
            co_to_codes[cid].add(str(r[c]))

    correct = []
    for _, r in df.iterrows():
        cid = r["CompanyId"]
        if pd.isna(cid):
            correct.append(False)
            continue
        correct.append(str(r["true_code"]) in co_to_codes[cid])
    return np.mean(correct), co_to_codes


def smart_rerank_against_real_segments(df, k=5):
    """For each row in a multi-code company, the model's top-k may include a code
    that matches the row's TRUE segment. If so, pick that one over the model's argmax.

    This is a STRONG operation — it uses oracle knowledge of the company's segment
    set. It's defensible if (and only if) we declare that at deploy time we have
    access to the company's existing GECS code coverage (which Morningstar's RED
    team often does for known companies). For brand-new companies it doesn't apply.
    """
    # Build CompanyId -> set of true codes seen in test (oracle company segment set)
    co_true_codes = defaultdict(set)
    for _, r in df.iterrows():
        if pd.notna(r["CompanyId"]):
            co_true_codes[r["CompanyId"]].add(str(r["true_code"]))

    topk_cols = [f"top{i}_code" for i in range(1, k + 1)]
    new_preds = []
    for _, r in df.iterrows():
        cid = r["CompanyId"]
        original = str(r["pred_code"])
        if pd.isna(cid) or cid not in co_true_codes:
            new_preds.append(original)
            continue
        company_codes = co_true_codes[cid]
        # If original prediction matches a real segment, keep it
        if original in company_codes:
            new_preds.append(original)
            continue
        # Otherwise, scan top-k for a candidate that matches a real segment
        for c in topk_cols:
            cand = str(r[c])
            if cand in company_codes:
                new_preds.append(cand)
                break
        else:
            new_preds.append(original)
    return new_preds


def revenue_weighted_company_pred(df, k=5):
    """For each company, aggregate top-k probabilities weighted by revenue_share
    across its rows. The argmax of the aggregated distribution is the company's
    single 'representative' prediction. Each row is then scored by whether the
    company prediction matches the row's true code.
    """
    topk_cols = [(f"top{i}_code", f"top{i}_prob") for i in range(1, k + 1)]
    df = df.copy()
    df["rs_clip"] = df["revenue_share"].clip(lower=0).fillna(0)

    co_scores = defaultdict(lambda: defaultdict(float))
    for _, r in df.iterrows():
        cid = r["CompanyId"]
        if pd.isna(cid):
            continue
        weight = r["rs_clip"] if r["rs_clip"] > 0 else 1.0  # fallback uniform
        for code_col, prob_col in topk_cols:
            co_scores[cid][str(r[code_col])] += weight * float(r[prob_col])

    co_pred = {cid: max(scores, key=scores.get) for cid, scores in co_scores.items()}
    df["pred_co_weighted"] = df["CompanyId"].map(co_pred)
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("topk_csv", type=str)
    args = ap.parse_args()

    print(f"Loading: {args.topk_csv}")
    pred = pd.read_csv(args.topk_csv)
    print(f"Loading: {ENRICHED}")
    enriched = pd.read_csv(ENRICHED)
    assert len(pred) == len(enriched), f"row count mismatch: {len(pred)} vs {len(enriched)}"

    df = enriched.copy()
    for c in pred.columns:
        df[c] = pred[c].values

    # Sanity
    headline_f1 = macro_f1(df["true_code"], df["pred_code"])
    headline_acc = (df["true_code"] == df["pred_code"]).mean()
    print(f"\nHeadline (top-1 argmax): macro F1 = {headline_f1:.4%}  acc = {headline_acc:.4%}")
    print(f"  (should match v3 final_summary 71.0324% F1)")

    # ========================================================================
    # 1. Top-k accuracy
    # ========================================================================
    print("\n=== TOP-K ACCURACY (row-level) ===")
    topk_arr = df[[f"top{i}_code" for i in range(1, 6)]].astype(str).values
    for k in (1, 2, 3, 5):
        acc = topk_accuracy(df["true_code"].astype(str).values, topk_arr[:, :k])
        print(f"  Top-{k} accuracy: {acc:.4%}")

    # By company kind
    print("\n  --- by company_kind ---")
    for kind in ("single_code", "multi_code"):
        sub = df[df["company_kind"] == kind]
        if len(sub) == 0:
            continue
        top1 = (sub["true_code"] == sub["pred_code"]).mean()
        top3 = topk_accuracy(
            sub["true_code"].astype(str).values,
            sub[[f"top{i}_code" for i in range(1, 4)]].astype(str).values,
        )
        top5 = topk_accuracy(
            sub["true_code"].astype(str).values,
            sub[[f"top{i}_code" for i in range(1, 6)]].astype(str).values,
        )
        print(f"  {kind:<15s} top1={top1:.2%}  top3={top3:.2%}  top5={top5:.2%}  n={len(sub)}")

    # ========================================================================
    # 2. Company-union top-k
    # ========================================================================
    print("\n=== COMPANY-UNION TOP-K (each row scored vs union of its company's top-k) ===")
    for k in (1, 3, 5):
        acc, _ = company_union_topk(df, k=k)
        print(f"  Company-union top-{k} accuracy: {acc:.4%}")

    # ========================================================================
    # 3. Revenue-weighted company prediction
    # ========================================================================
    print("\n=== REVENUE-SHARE-WEIGHTED COMPANY PREDICTION ===")
    df_w = revenue_weighted_company_pred(df, k=5)
    s = df_w.dropna(subset=["pred_co_weighted"])
    f1 = macro_f1(s["true_code"], s["pred_co_weighted"])
    acc = (s["true_code"].astype(str) == s["pred_co_weighted"].astype(str)).mean()
    print(f"  Full set (n={len(s)}): macro F1 = {f1:.4%}  acc = {acc:.4%}")

    # ========================================================================
    # 4. Smart rerank against real company segments (oracle)
    # ========================================================================
    print("\n=== SMART RERANK (oracle: pick top-k candidate matching a real company segment) ===")
    print("  WARNING: uses oracle knowledge of company's segment set. Defensible only")
    print("  for known companies (Morningstar RED workflow), not new ones.")
    new_preds = smart_rerank_against_real_segments(df, k=5)
    df_r = df.copy()
    df_r["pred_smart"] = new_preds
    f1_r = macro_f1(df_r["true_code"], df_r["pred_smart"])
    acc_r = (df_r["true_code"].astype(str) == df_r["pred_smart"].astype(str)).mean()
    print(f"  Smart rerank:    macro F1 = {f1_r:.4%}  acc = {acc_r:.4%}")
    n_changed = (df["pred_code"].astype(str) != df_r["pred_smart"].astype(str)).sum()
    n_now_correct = (
        (df["pred_code"].astype(str) != df["true_code"].astype(str))
        & (df_r["pred_smart"].astype(str) == df["true_code"].astype(str))
    ).sum()
    print(f"  Rows whose prediction changed:    {n_changed}")
    print(f"  Rows that became correct via rerank: {n_now_correct}")

    # By kind
    print("\n  --- smart rerank by company_kind ---")
    for kind in ("single_code", "multi_code"):
        sub = df_r[df_r["company_kind"] == kind]
        if len(sub) == 0:
            continue
        f1 = macro_f1(sub["true_code"], sub["pred_smart"])
        acc = (sub["true_code"].astype(str) == sub["pred_smart"].astype(str)).mean()
        print(f"  {kind:<15s} acc={acc:.2%}  macroF1={f1:.2%}  n={len(sub)}")


if __name__ == "__main__":
    main()
