from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from scipy.sparse import hstack as sparse_hstack


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL_DIR = ROOT / "models_segment_aware"


def _softmax(scores: np.ndarray) -> np.ndarray:
    scores = np.asarray(scores, dtype=np.float64)
    scores = scores - scores.max()
    exp_scores = np.exp(scores)
    return exp_scores / exp_scores.sum()


def load_segment_aware_assets(model_dir: Path | str = DEFAULT_MODEL_DIR) -> dict[str, Any]:
    model_dir = Path(model_dir)
    assets = {
        "model": joblib.load(model_dir / "task1_segment_aware_model.joblib"),
        "segment_word_vectorizer": joblib.load(model_dir / "task1_segment_word_vec.pkl"),
        "segment_char_vectorizer": joblib.load(model_dir / "task1_segment_char_vec.pkl"),
        "company_word_vectorizer": None,
        "manifest": {},
    }
    company_vec_path = model_dir / "task1_company_word_vec.pkl"
    if company_vec_path.exists():
        assets["company_word_vectorizer"] = joblib.load(company_vec_path)
    manifest_path = model_dir / "task1_segment_aware_manifest.json"
    if manifest_path.exists():
        assets["manifest"] = json.loads(manifest_path.read_text(encoding="utf-8"))
    return assets


def predict_segment_aware(
    company_text: str,
    segment_text: str,
    assets: dict[str, Any],
    top_n: int = 3,
) -> dict[str, Any]:
    manifest = assets.get("manifest", {})
    aux_weight = float(manifest.get("aux_weight", 0.0))

    parts = [
        assets["segment_word_vectorizer"].transform([segment_text]),
        assets["segment_char_vectorizer"].transform([segment_text]),
    ]
    if assets.get("company_word_vectorizer") is not None and company_text:
        parts.append(assets["company_word_vectorizer"].transform([company_text]).multiply(aux_weight))

    X_row = sparse_hstack(parts, format="csr")
    model = assets["model"]
    scores = model.decision_function(X_row)
    classes = np.asarray(model.classes_, dtype=str)
    margins = np.asarray(scores[0] if np.ndim(scores) > 1 else scores, dtype=np.float64)
    probs = _softmax(margins)
    order = np.argsort(probs)[::-1][:top_n]

    alternatives = [
        {
            "rank": int(rank) + 1,
            "code": str(classes[idx]),
            "confidence": round(float(probs[idx]) * 100.0, 1),
        }
        for rank, idx in enumerate(order)
    ]
    best_idx = int(order[0])
    return {
        "mstar_code": str(classes[best_idx]),
        "confidence": round(float(probs[best_idx]) * 100.0, 1),
        "alternatives": alternatives,
        "engine": "Task1 Segment-Aware Text Model",
        "route_reason": "Primary deployable text-only classifier selected from validation on the official train split.",
    }
