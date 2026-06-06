from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
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

from scripts.task1_segment_aware_common import build_task1_segment_aware_splits, save_json


OUT_DIR = ROOT / "models_company_aggregated"


def compute_metrics(true_codes: list[str], preds: list[str]) -> dict[str, Any]:
    macro_f1 = f1_score(true_codes, preds, average="macro", zero_division=0)
    acc = sum(p == t for p, t in zip(preds, true_codes)) / len(true_codes)
    cf = Counter(true_codes)
    top10 = [c for c, _ in cf.most_common(10)]
    top10_f1s = f1_score(true_codes, preds, average=None, labels=top10, zero_division=0)
    top10_pass = int(sum(1 for value in top10_f1s if value > 0.85))
    return {"macro_f1": float(macro_f1), "accuracy": float(acc), "top10_pass": top10_pass}


def build_company_examples(frame: pd.DataFrame, top_k_segments: int) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for company_id, group in frame.groupby("CompanyId", dropna=False):
        group = group.copy()
        group["segment_len"] = group["segment_text"].astype(str).str.len()
        group = group.sort_values(
            ["is_largest_share_segment", "revenue_share", "segment_len"],
            ascending=[False, False, False],
        )
        dominant_counts = group["code"].astype(str).value_counts()
        dominant_code = str(dominant_counts.index[0])
        dominant_share = float(dominant_counts.iloc[0] / len(group))
        company_text = max(group["company_text"].astype(str), key=len)
        top_segments = [text for text in group["segment_text"].astype(str).tolist() if text][:top_k_segments]
        stacked_segments = " [SEG] ".join(top_segments)
        full_text = (company_text + " [COMPANY] " + stacked_segments).strip()
        rows.append(
            {
                "CompanyId": company_id,
                "code": dominant_code,
                "full_text": full_text,
                "company_text": company_text,
                "stacked_segments": stacked_segments,
                "company_num_codes": int(group["company_num_codes"].iloc[0]),
                "company_dominant_share": dominant_share,
                "sample_weight": float(group["sample_weight"].mean() * dominant_share),
                "row_count": int(len(group)),
            }
        )
    return pd.DataFrame(rows)


def maybe_load_enriched_splits() -> tuple[pd.DataFrame, pd.DataFrame]:
    train_path = ROOT / "models_segment_aware" / "task1_train_enriched.csv"
    test_path = ROOT / "models_segment_aware" / "task1_test_enriched.csv"
    if train_path.exists() and test_path.exists():
        return pd.read_csv(train_path), pd.read_csv(test_path)
    train, test, _ = build_task1_segment_aware_splits()
    return train, test


def main() -> None:
    parser = argparse.ArgumentParser(description="Train company-aggregated Task 1 model.")
    parser.add_argument("--top-k-segments", type=int, default=5)
    parser.add_argument("--val-frac", type=float, default=0.10)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--max-word-features", type=int, default=120000)
    parser.add_argument("--max-char-features", type=int, default=60000)
    parser.add_argument("--quick", action="store_true")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    train_rows, test_rows = maybe_load_enriched_splits()
    train_companies = build_company_examples(train_rows, args.top_k_segments)
    test_companies = build_company_examples(test_rows, args.top_k_segments)

    fit_df, val_df = train_test_split(
        train_companies,
        test_size=args.val_frac,
        random_state=args.seed,
        stratify=train_companies["code"],
    )

    vec_word = TfidfVectorizer(
        max_features=args.max_word_features,
        sublinear_tf=True,
        stop_words="english",
        ngram_range=(1, 2),
        min_df=2,
    )
    vec_char = TfidfVectorizer(
        max_features=args.max_char_features,
        sublinear_tf=True,
        analyzer="char_wb",
        ngram_range=(3, 5),
        min_df=2,
    )

    X_fit_word = vec_word.fit_transform(fit_df["full_text"])
    X_val_word = vec_word.transform(val_df["full_text"])
    X_test_word = vec_word.transform(test_companies["full_text"])

    X_fit_char = vec_char.fit_transform(fit_df["full_text"])
    X_val_char = vec_char.transform(val_df["full_text"])
    X_test_char = vec_char.transform(test_companies["full_text"])

    from scipy.sparse import hstack as sparse_hstack

    X_fit = sparse_hstack([X_fit_word, X_fit_char], format="csr")
    X_val = sparse_hstack([X_val_word, X_val_char], format="csr")
    X_test = sparse_hstack([X_test_word, X_test_char], format="csr")

    c_grid = [1.0] if args.quick else [0.5, 1.0, 2.0]
    best: dict[str, Any] | None = None
    candidate_rows: list[dict[str, Any]] = []

    print("Training company-aggregated candidates...", flush=True)
    print(
        f"  train_companies={len(train_companies):,}  test_companies={len(test_companies):,}  "
        f"overlapping_company_ids_not_removed_by_official_split=allowed",
        flush=True,
    )

    for weight_mode in (["uniform"] if args.quick else ["uniform", "ambiguity_aware"]):
        sample_weights = None if weight_mode == "uniform" else fit_df["sample_weight"].to_numpy()
        for c_value in c_grid:
            clf = LinearSVC(C=c_value, dual=False, class_weight="balanced", max_iter=5000)
            started = time.time()
            if sample_weights is None:
                clf.fit(X_fit, fit_df["code"].to_numpy())
            else:
                clf.fit(X_fit, fit_df["code"].to_numpy(), sample_weight=sample_weights)
            val_preds = clf.predict(X_val)
            val_metrics = compute_metrics(val_df["code"].astype(str).tolist(), list(val_preds))
            row = {
                "classifier": "LinearSVC",
                "sample_weight_mode": weight_mode,
                "C": c_value,
                "val_macro_f1": val_metrics["macro_f1"],
                "val_accuracy": val_metrics["accuracy"],
                "val_top10_pass": val_metrics["top10_pass"],
                "elapsed_seconds": round(time.time() - started, 1),
            }
            candidate_rows.append(row)
            print(
                f"  CompanyAgg C={c_value:g} weight={weight_mode}: "
                f"F1={val_metrics['macro_f1']*100:6.2f}%  acc={val_metrics['accuracy']*100:6.2f}%  "
                f"top10={val_metrics['top10_pass']}/10",
                flush=True,
            )
            if best is None or (
                row["val_macro_f1"],
                row["val_top10_pass"],
                row["val_accuracy"],
            ) > (
                best["val_macro_f1"],
                best["val_top10_pass"],
                best["val_accuracy"],
            ):
                best = row

    if best is None:
        raise RuntimeError("No company-aggregated candidates were evaluated.")

    X_train_word = vec_word.fit_transform(train_companies["full_text"])
    X_train_char = vec_char.fit_transform(train_companies["full_text"])
    X_train = sparse_hstack([X_train_word, X_train_char], format="csr")
    X_test_word = vec_word.transform(test_companies["full_text"])
    X_test_char = vec_char.transform(test_companies["full_text"])
    X_test = sparse_hstack([X_test_word, X_test_char], format="csr")

    final_clf = LinearSVC(C=float(best["C"]), dual=False, class_weight="balanced", max_iter=5000)
    final_weights = None if best["sample_weight_mode"] == "uniform" else train_companies["sample_weight"].to_numpy()
    if final_weights is None:
        final_clf.fit(X_train, train_companies["code"].to_numpy())
    else:
        final_clf.fit(X_train, train_companies["code"].to_numpy(), sample_weight=final_weights)

    company_preds = final_clf.predict(X_test)
    company_metrics = compute_metrics(test_companies["code"].astype(str).tolist(), list(company_preds))

    company_pred_map = dict(zip(test_companies["CompanyId"].astype(str), company_preds))
    row_preds = test_rows["CompanyId"].astype(str).map(company_pred_map).fillna("")
    row_metrics = compute_metrics(test_rows["code"].astype(str).tolist(), row_preds.tolist())

    joblib.dump(final_clf, OUT_DIR / "task1_company_aggregated_model.joblib")
    joblib.dump(vec_word, OUT_DIR / "task1_company_aggregated_word_vec.pkl")
    joblib.dump(vec_char, OUT_DIR / "task1_company_aggregated_char_vec.pkl")

    summary = {
        "version": "task1-company-aggregated-v1",
        "top_k_segments": args.top_k_segments,
        "candidate_grid": candidate_rows,
        "selected_candidate": best,
        "company_level_test": {
            "macro_f1": round(company_metrics["macro_f1"] * 100, 2),
            "accuracy": round(company_metrics["accuracy"] * 100, 2),
            "top10_pass": int(company_metrics["top10_pass"]),
        },
        "row_level_projection_test": {
            "macro_f1": round(row_metrics["macro_f1"] * 100, 2),
            "accuracy": round(row_metrics["accuracy"] * 100, 2),
            "top10_pass": int(row_metrics["top10_pass"]),
        },
    }
    save_json(summary, OUT_DIR / "training_summary.json")
    pd.DataFrame(candidate_rows).sort_values("val_macro_f1", ascending=False).to_csv(
        OUT_DIR / "candidate_grid.csv",
        index=False,
    )
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == "__main__":
    main()
