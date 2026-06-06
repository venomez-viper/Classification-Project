from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from scipy.sparse import hstack as sparse_hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
from sklearn.model_selection import train_test_split
from sklearn.svm import LinearSVC

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task1_segment_aware_common import build_task1_segment_aware_splits, save_json

OUT_DIR = ROOT / "models_segment_aware"


def parse_float_grid(text: str) -> list[float]:
    return [float(part.strip()) for part in text.split(",") if part.strip()]


def compute_metrics(true_codes: list[str], preds: list[str]) -> dict[str, Any]:
    macro_f1 = f1_score(true_codes, preds, average="macro", zero_division=0)
    acc = sum(p == t for p, t in zip(preds, true_codes)) / len(true_codes)
    cf = Counter(true_codes)
    top10 = [c for c, _ in cf.most_common(10)]
    top10_f1s = f1_score(true_codes, preds, average=None, labels=top10, zero_division=0)
    top10_pass = int(sum(1 for value in top10_f1s if value > 0.85))
    return {
        "macro_f1": float(macro_f1),
        "accuracy": float(acc),
        "top10_pass": top10_pass,
    }


def print_metrics(prefix: str, metrics: dict[str, Any]) -> None:
    print(
        f"{prefix} F1={metrics['macro_f1']*100:6.2f}%  "
        f"acc={metrics['accuracy']*100:6.2f}%  top10={metrics['top10_pass']}/10",
        flush=True,
    )


def build_feature_bundle(
    fit_df: pd.DataFrame,
    target_frames: dict[str, pd.DataFrame],
    aux_weight: float,
    max_seg_word_features: int,
    max_seg_char_features: int,
    max_company_features: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    seg_word = TfidfVectorizer(
        max_features=max_seg_word_features,
        sublinear_tf=True,
        stop_words="english",
        ngram_range=(1, 2),
        min_df=2,
    )
    seg_char = TfidfVectorizer(
        max_features=max_seg_char_features,
        sublinear_tf=True,
        analyzer="char_wb",
        ngram_range=(3, 5),
        min_df=2,
    )
    company_word = None
    if aux_weight > 0:
        company_word = TfidfVectorizer(
            max_features=max_company_features,
            sublinear_tf=True,
            stop_words="english",
            ngram_range=(1, 2),
            min_df=2,
        )

    seg_word_fit = seg_word.fit_transform(fit_df["segment_text"])
    seg_char_fit = seg_char.fit_transform(fit_df["segment_text"])
    company_fit = company_word.fit_transform(fit_df["company_text"]) if company_word else None

    def transform(frame: pd.DataFrame):
        parts = [
            seg_word.transform(frame["segment_text"]),
            seg_char.transform(frame["segment_text"]),
        ]
        if company_word is not None:
            parts.append(company_word.transform(frame["company_text"]).multiply(aux_weight))
        return sparse_hstack(parts, format="csr")

    matrices = {name: transform(frame) for name, frame in target_frames.items()}
    matrices["fit"] = sparse_hstack(
        [
            seg_word_fit,
            seg_char_fit,
            company_fit.multiply(aux_weight) if company_fit is not None else None,
        ],
        format="csr",
    ) if company_fit is not None else sparse_hstack([seg_word_fit, seg_char_fit], format="csr")

    assets = {
        "segment_word_vectorizer": seg_word,
        "segment_char_vectorizer": seg_char,
        "company_word_vectorizer": company_word,
        "aux_weight": aux_weight,
    }
    return matrices, assets


def fit_and_score(
    classifier_name: str,
    classifier,
    X_train,
    y_train: np.ndarray,
    X_eval,
    y_eval: list[str],
    sample_weights: np.ndarray | None,
) -> dict[str, Any]:
    started = time.time()
    if sample_weights is None:
        classifier.fit(X_train, y_train)
    else:
        classifier.fit(X_train, y_train, sample_weight=sample_weights)
    preds = classifier.predict(X_eval)
    metrics = compute_metrics(y_eval, list(preds))
    metrics["classifier_name"] = classifier_name
    metrics["elapsed_seconds"] = round(time.time() - started, 1)
    metrics["estimator"] = classifier
    return metrics


def maybe_load_enriched_splits() -> tuple[pd.DataFrame, pd.DataFrame]:
    train_path = OUT_DIR / "task1_train_enriched.csv"
    test_path = OUT_DIR / "task1_test_enriched.csv"
    if train_path.exists() and test_path.exists():
        return pd.read_csv(train_path), pd.read_csv(test_path)
    train, test, summary = build_task1_segment_aware_splits()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    train.to_csv(train_path, index=False)
    test.to_csv(test_path, index=False)
    save_json(summary, OUT_DIR / "company_ambiguity_summary.json")
    return train, test


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Train ambiguity-aware Task 1 text-only classifier.")
    parser.add_argument("--val-frac", type=float, default=0.10)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--aux-weights", type=str, default="0.0,0.15,0.30,0.45")
    parser.add_argument("--svc-cs", type=str, default="0.5,1.0,2.0")
    parser.add_argument("--include-logreg", action="store_true")
    parser.add_argument("--max-seg-word-features", type=int, default=90000)
    parser.add_argument("--max-seg-char-features", type=int, default=50000)
    parser.add_argument("--max-company-features", type=int, default=30000)
    parser.add_argument("--quick", action="store_true")
    return parser


def main() -> None:
    args = make_parser().parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    train_df, test_df = maybe_load_enriched_splits()
    train_df["code"] = train_df["code"].astype(str)
    test_df["code"] = test_df["code"].astype(str)

    fit_df, val_df = train_test_split(
        train_df,
        test_size=args.val_frac,
        random_state=args.seed,
        stratify=train_df["code"],
    )
    fit_df = fit_df.reset_index(drop=True)
    val_df = val_df.reset_index(drop=True)
    test_df = test_df.reset_index(drop=True)

    aux_weights = [0.0, 0.30] if args.quick else parse_float_grid(args.aux_weights)
    svc_cs = [1.0] if args.quick else parse_float_grid(args.svc_cs)
    sample_weight_modes = ["uniform"] if args.quick else ["uniform", "ambiguity_aware"]

    print("Training Task 1 segment-aware candidates...", flush=True)
    print(
        f"  fit={len(fit_df):,}  val={len(val_df):,}  test={len(test_df):,}  "
        f"codes={train_df['code'].nunique()}",
        flush=True,
    )

    candidate_rows: list[dict[str, Any]] = []
    best_candidate: dict[str, Any] | None = None

    for aux_weight in aux_weights:
        matrices, _ = build_feature_bundle(
            fit_df=fit_df,
            target_frames={"val": val_df},
            aux_weight=aux_weight,
            max_seg_word_features=args.max_seg_word_features,
            max_seg_char_features=args.max_seg_char_features,
            max_company_features=args.max_company_features,
        )
        X_fit = matrices["fit"]
        X_val = matrices["val"]
        y_fit = fit_df["code"].to_numpy(dtype=str)
        y_val = val_df["code"].astype(str).tolist()

        for sample_weight_mode in sample_weight_modes:
            sample_weights = None
            if sample_weight_mode == "ambiguity_aware":
                sample_weights = fit_df["sample_weight"].to_numpy(dtype=np.float64)

            for c_value in svc_cs:
                clf_name = f"LinearSVC(aux={aux_weight:.2f}, weight={sample_weight_mode}, C={c_value:g})"
                print(f"\nEvaluating {clf_name}", flush=True)
                clf = LinearSVC(C=c_value, dual=False, class_weight="balanced", max_iter=5000)
                result = fit_and_score(clf_name, clf, X_fit, y_fit, X_val, y_val, sample_weights)
                print_metrics("  val", result)
                row = {
                    "classifier": "LinearSVC",
                    "aux_weight": aux_weight,
                    "sample_weight_mode": sample_weight_mode,
                    "C": c_value,
                    "val_macro_f1": result["macro_f1"],
                    "val_accuracy": result["accuracy"],
                    "val_top10_pass": result["top10_pass"],
                    "elapsed_seconds": result["elapsed_seconds"],
                }
                candidate_rows.append(row)
                if best_candidate is None or (
                    result["macro_f1"],
                    result["top10_pass"],
                    result["accuracy"],
                ) > (
                    best_candidate["val_macro_f1"],
                    best_candidate["val_top10_pass"],
                    best_candidate["val_accuracy"],
                ):
                    best_candidate = row

            if args.include_logreg and aux_weight in {0.0, 0.30}:
                clf_name = f"LogReg(aux={aux_weight:.2f}, weight={sample_weight_mode})"
                print(f"\nEvaluating {clf_name}", flush=True)
                clf = LogisticRegression(
                    C=1.0,
                    class_weight="balanced",
                    solver="saga",
                    max_iter=1500,
                    n_jobs=-1,
                    verbose=0,
                )
                result = fit_and_score(clf_name, clf, X_fit, y_fit, X_val, y_val, sample_weights)
                print_metrics("  val", result)
                row = {
                    "classifier": "LogisticRegression",
                    "aux_weight": aux_weight,
                    "sample_weight_mode": sample_weight_mode,
                    "C": 1.0,
                    "val_macro_f1": result["macro_f1"],
                    "val_accuracy": result["accuracy"],
                    "val_top10_pass": result["top10_pass"],
                    "elapsed_seconds": result["elapsed_seconds"],
                }
                candidate_rows.append(row)
                if best_candidate is None or (
                    result["macro_f1"],
                    result["top10_pass"],
                    result["accuracy"],
                ) > (
                    best_candidate["val_macro_f1"],
                    best_candidate["val_top10_pass"],
                    best_candidate["val_accuracy"],
                ):
                    best_candidate = row

    if best_candidate is None:
        raise RuntimeError("No candidate models were evaluated.")

    print("\nSelected validation winner:", flush=True)
    print(json.dumps(best_candidate, indent=2), flush=True)

    full_matrices, assets = build_feature_bundle(
        fit_df=train_df,
        target_frames={"test": test_df},
        aux_weight=float(best_candidate["aux_weight"]),
        max_seg_word_features=args.max_seg_word_features,
        max_seg_char_features=args.max_seg_char_features,
        max_company_features=args.max_company_features,
    )
    X_train_full = full_matrices["fit"]
    X_test = full_matrices["test"]
    y_train_full = train_df["code"].to_numpy(dtype=str)
    y_test = test_df["code"].astype(str).tolist()

    sample_weights_full = None
    if best_candidate["sample_weight_mode"] == "ambiguity_aware":
        sample_weights_full = train_df["sample_weight"].to_numpy(dtype=np.float64)

    if best_candidate["classifier"] == "LinearSVC":
        final_estimator = LinearSVC(
            C=float(best_candidate["C"]),
            dual=False,
            class_weight="balanced",
            max_iter=5000,
        )
    else:
        final_estimator = LogisticRegression(
            C=float(best_candidate["C"]),
            class_weight="balanced",
            solver="saga",
            max_iter=1500,
            n_jobs=-1,
            verbose=0,
        )

    print("\nRetraining winner on full official train split...", flush=True)
    final_result = fit_and_score(
        "final",
        final_estimator,
        X_train_full,
        y_train_full,
        X_test,
        y_test,
        sample_weights_full,
    )
    print_metrics("  test", final_result)

    joblib.dump(final_result["estimator"], OUT_DIR / "task1_segment_aware_model.joblib")
    joblib.dump(assets["segment_word_vectorizer"], OUT_DIR / "task1_segment_word_vec.pkl")
    joblib.dump(assets["segment_char_vectorizer"], OUT_DIR / "task1_segment_char_vec.pkl")
    if assets["company_word_vectorizer"] is not None:
        joblib.dump(assets["company_word_vectorizer"], OUT_DIR / "task1_company_word_vec.pkl")

    manifest = {
        "model_name": "task1-segment-aware-text",
        "artifact_dir": str(OUT_DIR.relative_to(ROOT)),
        "classifier": best_candidate["classifier"],
        "sample_weight_mode": best_candidate["sample_weight_mode"],
        "aux_weight": float(best_candidate["aux_weight"]),
        "feature_contract": {
            "segment_text_required": True,
            "company_text_optional": True,
            "numerical_features_required": False,
        },
        "evaluation": {
            "validation_macro_f1": round(float(best_candidate["val_macro_f1"]) * 100, 2),
            "official_test_macro_f1": round(float(final_result["macro_f1"]) * 100, 2),
            "official_test_accuracy": round(float(final_result["accuracy"]) * 100, 2),
            "official_test_top10_pass": int(final_result["top10_pass"]),
        },
    }
    save_json(manifest, OUT_DIR / "task1_segment_aware_manifest.json")

    summary = {
        "version": "task1-segment-aware-text-v1",
        "selection_protocol": {
            "official_train_split_rows": int(len(train_df)),
            "validation_fraction_within_train": args.val_frac,
            "official_test_rows": int(len(test_df)),
        },
        "candidate_grid": candidate_rows,
        "selected_candidate": best_candidate,
        "official_test_result": {
            "macro_f1": round(float(final_result["macro_f1"]) * 100, 2),
            "accuracy": round(float(final_result["accuracy"]) * 100, 2),
            "top10_pass": int(final_result["top10_pass"]),
        },
        "artifacts": {
            "model": "models_segment_aware/task1_segment_aware_model.joblib",
            "segment_word_vectorizer": "models_segment_aware/task1_segment_word_vec.pkl",
            "segment_char_vectorizer": "models_segment_aware/task1_segment_char_vec.pkl",
            "company_word_vectorizer": (
                "models_segment_aware/task1_company_word_vec.pkl"
                if assets["company_word_vectorizer"] is not None
                else None
            ),
            "manifest": "models_segment_aware/task1_segment_aware_manifest.json",
        },
    }
    save_json(summary, OUT_DIR / "training_summary.json")
    pd.DataFrame(candidate_rows).sort_values("val_macro_f1", ascending=False).to_csv(
        OUT_DIR / "candidate_grid.csv",
        index=False,
    )

    print(f"\nSaved model + manifests to {OUT_DIR}", flush=True)


if __name__ == "__main__":
    main()
