"""Ensemble N model prediction CSVs (each with top-5 codes + probs) into a single
final prediction by geometric-mean of per-class probabilities.

Usage:
    python scripts/ensemble_models.py \
        --task 1 \
        --inputs path1.csv path2.csv path3.csv \
        --weights 1.0 1.0 0.7 \
        --out ensemble_predictions.csv

Then run: python scripts/analyze_topk.py ensemble_predictions.csv
"""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, accuracy_score
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent


def normalize_code(v, width):
    if pd.isna(v): return None
    s = str(v).strip()
    if s.endswith(".0"): s = s[:-2]
    digits = "".join(ch for ch in s if ch.isdigit())
    return digits.zfill(width) if digits else None


def load_topk(path: Path, code_width: int) -> pd.DataFrame:
    df = pd.read_csv(path)
    needed = ["true_code", "pred_code"] + [f"top{i}_code" for i in range(1, 6)] + [f"top{i}_prob" for i in range(1, 6)]
    missing = [c for c in needed if c not in df.columns]
    if missing:
        raise SystemExit(f"{path} missing columns: {missing}")
    for c in ["true_code", "pred_code"] + [f"top{i}_code" for i in range(1, 6)]:
        df[c] = df[c].map(lambda v: normalize_code(v, code_width))
    return df


def ensemble_geomean(dfs, weights, all_codes):
    """Geometric mean of per-row, per-class probabilities."""
    n_rows = len(dfs[0])
    n_classes = len(all_codes)
    code_to_idx = {c: i for i, c in enumerate(all_codes)}
    log_acc = np.full((n_rows, n_classes), -1e9, dtype=np.float64)  # log(0) ~ -inf

    for df, w in zip(dfs, weights):
        # Build per-row log-prob array (only top-5 are populated; rest stay -inf)
        log_probs = np.full((n_rows, n_classes), -1e9, dtype=np.float64)
        for k in range(1, 6):
            codes = df[f"top{k}_code"].values
            probs = df[f"top{k}_prob"].astype(float).values
            for i, c in enumerate(codes):
                if c is None or c not in code_to_idx:
                    continue
                idx = code_to_idx[c]
                lp = np.log(max(probs[i], 1e-12))
                # Take max if same class appears multiple times in top-5 (shouldn't but safe)
                if log_probs[i, idx] < lp:
                    log_probs[i, idx] = lp
        # Add weighted log-prob
        log_acc = np.logaddexp(log_acc, np.log(w) + log_probs) if False else log_acc + w * log_probs
        # Note: above is geometric mean of weighted probabilities (sum of w*log_p)

    # Argmax of log_acc → predicted code
    pred_idx = log_acc.argmax(axis=1)
    pred_codes = np.array([all_codes[i] for i in pred_idx])

    # Top-5 from ensemble
    top5_idx = np.argsort(-log_acc, axis=1)[:, :5]
    top5_codes = np.array([[all_codes[j] for j in row] for row in top5_idx])
    top5_logp = np.take_along_axis(log_acc, top5_idx, axis=1)
    # Convert to softmax-ish probs over top-5
    top5_probs_raw = np.exp(top5_logp - top5_logp.max(axis=1, keepdims=True))
    top5_probs = top5_probs_raw / top5_probs_raw.sum(axis=1, keepdims=True)

    return pred_codes, top5_codes, top5_probs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", type=int, choices=[1, 2], default=1)
    ap.add_argument("--inputs", nargs="+", required=True, help="prediction CSVs (top-5 + probs format)")
    ap.add_argument("--weights", nargs="+", type=float, default=None)
    ap.add_argument("--out", type=str, required=True)
    args = ap.parse_args()

    code_width = 8 if args.task == 1 else 10
    weights = args.weights or [1.0] * len(args.inputs)
    assert len(weights) == len(args.inputs), "weights count must match inputs count"
    print(f"Ensembling {len(args.inputs)} models, weights={weights}, code_width={code_width}")

    dfs = [load_topk(Path(p), code_width) for p in args.inputs]
    n = len(dfs[0])
    for d in dfs[1:]:
        assert len(d) == n, f"row count mismatch: {n} vs {len(d)}"
    print(f"Rows per model: {n}")

    # Sanity: true codes should match across all CSVs
    true0 = dfs[0]["true_code"].values
    for i, d in enumerate(dfs[1:], start=1):
        if not (d["true_code"].values == true0).all():
            mismatches = (d["true_code"].values != true0).sum()
            print(f"  WARN: input {i} has {mismatches} true_code mismatches with input 0")

    # Universe of codes = union across all top-5 predictions + true labels
    all_codes = set()
    for d in dfs:
        for k in range(1, 6):
            all_codes.update(d[f"top{k}_code"].dropna().tolist())
        all_codes.update(d["true_code"].dropna().tolist())
    all_codes = sorted(all_codes)
    print(f"Code universe: {len(all_codes)}")

    pred_codes, top5_codes, top5_probs = ensemble_geomean(dfs, weights, all_codes)

    out_df = pd.DataFrame({"true_code": true0, "pred_code": pred_codes})
    for k in range(5):
        out_df[f"top{k+1}_code"] = top5_codes[:, k]
        out_df[f"top{k+1}_prob"] = top5_probs[:, k]
    out_df.to_csv(args.out, index=False)
    print(f"Wrote {args.out}")

    f1 = f1_score(true0, pred_codes, average="macro", zero_division=0)
    acc = accuracy_score(true0, pred_codes)
    print(f"\nENSEMBLE TEST: macro F1 = {f1:.4%}  acc = {acc:.4%}")
    # Also report individual baselines
    print("\nFor comparison (individual model headlines):")
    for path, d in zip(args.inputs, dfs):
        f1_i = f1_score(d["true_code"], d["pred_code"], average="macro", zero_division=0)
        acc_i = accuracy_score(d["true_code"], d["pred_code"])
        print(f"  {Path(path).name}: F1 = {f1_i:.4%}  acc = {acc_i:.4%}")


if __name__ == "__main__":
    main()
