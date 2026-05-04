from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np

from scripts.cascade_common import DEFAULT_HIERARCHY_JSON, DEFAULT_MODELS_DIR


VECTORIZER_NAME = "cascade_vectorizer.pkl"
L1_NAME = "cascade_L1_svm.joblib"
L2_NAME = "cascade_L2_models.joblib"
L3_NAME = "cascade_L3_models.joblib"
SUMMARY_NAME = "cascade_training_summary.json"


def _softmax(scores: np.ndarray) -> np.ndarray:
    scores = np.asarray(scores, dtype=np.float64)
    scores = scores - scores.max()
    exp_scores = np.exp(scores)
    return exp_scores / exp_scores.sum()


def _rank_artifact(artifact: dict[str, Any], X_sparse, top_n: int = 3) -> tuple[str, float, list[dict[str, Any]]]:
    if artifact["type"] == "constant":
        label = str(artifact["value"])
        alternatives = [{"rank": 1, "label": label, "confidence": 100.0}]
        return label, 100.0, alternatives

    model = artifact["model"]
    scores = model.decision_function(X_sparse)
    classes = np.asarray(model.classes_, dtype=str)

    if np.ndim(scores) == 1:
        margins = np.array([-scores[0], scores[0]], dtype=np.float64)
    else:
        margins = np.asarray(scores[0], dtype=np.float64)

    probs = _softmax(margins)
    order = np.argsort(probs)[::-1][:top_n]
    alternatives = [
        {
            "rank": int(rank) + 1,
            "label": str(classes[idx]),
            "confidence": round(float(probs[idx]) * 100.0, 1),
        }
        for rank, idx in enumerate(order)
    ]
    best_idx = int(order[0])
    return str(classes[best_idx]), round(float(probs[best_idx]) * 100.0, 1), alternatives


def load_cascade_assets(
    models_dir: Path | str = DEFAULT_MODELS_DIR,
    hierarchy_path: Path | str = DEFAULT_HIERARCHY_JSON,
) -> dict[str, Any]:
    models_dir = Path(models_dir)
    hierarchy_path = Path(hierarchy_path)

    assets = {
        "vectorizer": joblib.load(models_dir / VECTORIZER_NAME),
        "l1": joblib.load(models_dir / L1_NAME),
        "l2": joblib.load(models_dir / L2_NAME),
        "l3": joblib.load(models_dir / L3_NAME),
        "summary": {},
        "hierarchy": {},
    }

    summary_path = models_dir / SUMMARY_NAME
    if summary_path.exists():
        assets["summary"] = json.loads(summary_path.read_text(encoding="utf-8"))
    if hierarchy_path.exists():
        assets["hierarchy"] = json.loads(hierarchy_path.read_text(encoding="utf-8"))
    return assets


def cascade_predict(text: str, assets: dict[str, Any], top_n: int = 3) -> dict[str, Any]:
    X_sparse = assets["vectorizer"].transform([text])
    return cascade_predict_sparse(X_sparse, assets, top_n=top_n)


def cascade_predict_sparse(X_sparse, assets: dict[str, Any], top_n: int = 3) -> dict[str, Any]:
    sector_code, sector_conf, sector_alts = _rank_artifact(assets["l1"], X_sparse, top_n=top_n)

    l2_artifact = assets["l2"].get(sector_code)
    if l2_artifact is None:
        raise KeyError(f"No level-2 artifact found for sector {sector_code}")
    group_code, group_conf, group_alts = _rank_artifact(l2_artifact, X_sparse, top_n=top_n)

    l3_artifact = assets["l3"].get(group_code)
    if l3_artifact is None:
        raise KeyError(f"No level-3 artifact found for group {group_code}")
    final_code, final_conf, final_alts = _rank_artifact(l3_artifact, X_sparse, top_n=top_n)

    return {
        "sector_code": sector_code,
        "group_code": group_code,
        "mstar_code": final_code,
        "confidence": round(min(sector_conf, group_conf, final_conf), 1),
        "confidence_path": {
            "sector": sector_conf,
            "group": group_conf,
            "code": final_conf,
        },
        "alternatives": {
            "sector": sector_alts,
            "group": group_alts,
            "code": final_alts,
        },
    }
