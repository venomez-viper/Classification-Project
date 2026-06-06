from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.cascade_common import (
    DEFAULT_HIERARCHY_JSON,
    DEFAULT_MODELS_DIR,
    DEFAULT_TASK1_CSV,
    build_taxonomy_tree,
    load_task1_training_frame,
    save_json,
)
from scripts.cascade_predict import L1_NAME, L2_NAME, L3_NAME, SUMMARY_NAME, VECTORIZER_NAME


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train a hierarchy-aware Task 1 cascade.")
    parser.add_argument("--input", default=str(DEFAULT_TASK1_CSV), help="Task 1 cleaned CSV path")
    parser.add_argument("--models-dir", default=str(DEFAULT_MODELS_DIR), help="Directory for cascade artifacts")
    parser.add_argument("--hierarchy-output", default=str(DEFAULT_HIERARCHY_JSON), help="Hierarchy JSON path")
    parser.add_argument("--max-features", type=int, default=50000, help="TF-IDF vocabulary size")
    parser.add_argument("--max-iter", type=int, default=5000, help="LinearSVC max_iter")
    return parser.parse_args()


def make_vectorizer(max_features: int) -> TfidfVectorizer:
    return TfidfVectorizer(
        max_features=max_features,
        sublinear_tf=True,
        stop_words="english",
        ngram_range=(1, 2),
    )


def fit_artifact(X_sparse, labels, max_iter: int) -> dict[str, Any]:
    unique = sorted({str(label) for label in labels})
    if len(unique) == 1:
        return {"type": "constant", "value": unique[0]}

    model = LinearSVC(class_weight="balanced", dual=False, max_iter=max_iter)
    model.fit(X_sparse, labels)
    return {"type": "svm", "model": model}


def main() -> None:
    args = parse_args()
    models_dir = Path(args.models_dir)
    models_dir.mkdir(parents=True, exist_ok=True)

    frame = load_task1_training_frame(args.input)
    hierarchy = build_taxonomy_tree(frame)
    save_json(hierarchy, args.hierarchy_output)

    vectorizer = make_vectorizer(args.max_features)
    X_sparse = vectorizer.fit_transform(frame["combined_text"])

    l1_artifact = fit_artifact(X_sparse, frame["sector_code"], max_iter=args.max_iter)

    l2_artifacts = {}
    for sector_code, sector_frame in frame.groupby("sector_code", sort=True):
        sector_mask = frame["sector_code"] == sector_code
        l2_artifacts[str(sector_code)] = fit_artifact(
            X_sparse[sector_mask.to_numpy()],
            sector_frame["group_code"],
            max_iter=args.max_iter,
        )

    l3_artifacts = {}
    for group_code, group_frame in frame.groupby("group_code", sort=True):
        group_mask = frame["group_code"] == group_code
        l3_artifacts[str(group_code)] = fit_artifact(
            X_sparse[group_mask.to_numpy()],
            group_frame["code"],
            max_iter=args.max_iter,
        )

    joblib.dump(vectorizer, models_dir / VECTORIZER_NAME)
    joblib.dump(l1_artifact, models_dir / L1_NAME)
    joblib.dump(l2_artifacts, models_dir / L2_NAME)
    joblib.dump(l3_artifacts, models_dir / L3_NAME)

    summary = {
        "rows": int(len(frame)),
        "sector_count": int(frame["sector_code"].nunique()),
        "group_count": int(frame["group_code"].nunique()),
        "code_count": int(frame["code"].nunique()),
        "vectorizer": {
            "max_features": args.max_features,
            "vocabulary_size": int(len(vectorizer.vocabulary_)),
            "ngram_range": [1, 2],
            "sublinear_tf": True,
            "stop_words": "english",
        },
        "artifacts": {
            "l1_type": l1_artifact["type"],
            "l2_total": int(len(l2_artifacts)),
            "l2_constants": int(sum(1 for item in l2_artifacts.values() if item["type"] == "constant")),
            "l3_total": int(len(l3_artifacts)),
            "l3_constants": int(sum(1 for item in l3_artifacts.values() if item["type"] == "constant")),
        },
    }
    (models_dir / SUMMARY_NAME).write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"Cascade artifacts saved to {models_dir}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
