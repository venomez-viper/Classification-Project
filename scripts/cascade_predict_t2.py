"""
Task 2 Sub-Industry Hybrid Cascade — Prediction Module

Architecture:
  Stage 1 — Task 1 cascade (L1->L2->L3) predicts MSTAR code
             Input:  LongProfile + SegmentName + SegmentDescription
  Stage 2 — L4 model predicts sub-industry within that MSTAR code
             Input:  SegmentName + SegmentDescription only

Result: 55.41% Macro F1 on 428 sub-industry classes (+19pp over DeBERTa)
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np

from pathlib import Path as _Path

from scripts.cascade_predict import load_cascade_assets, _rank_artifact

# Artifact filenames — kept in sync with train_cascade_t2.py
T2_L4_SEG_VEC = "t2_cascade_seg_vec.pkl"
T2_L4_SEG     = "t2_cascade_L4_seg.joblib"
T2_SUMMARY    = "t2_cascade_summary.json"
DEFAULT_MODELS = _Path(__file__).resolve().parents[1] / "models"


def _softmax(scores: np.ndarray) -> np.ndarray:
    s = np.asarray(scores, dtype=np.float64)
    s = s - s.max()
    e = np.exp(s)
    return e / e.sum()


def _rank_l4(artifact: dict, X_row, top_n: int = 3) -> tuple[str, float, list[dict]]:
    if artifact["type"] == "constant":
        label = str(artifact["value"])
        return label, 100.0, [{"rank": 1, "label": label, "confidence": 100.0}]
    clf    = artifact["model"]
    scores = clf.decision_function(X_row)
    margins = np.asarray(scores[0] if np.ndim(scores) > 1 else scores, dtype=np.float64)
    probs   = _softmax(margins)
    order   = np.argsort(probs)[::-1][:top_n]
    alts    = [
        {"rank": int(r) + 1, "label": str(clf.classes_[i]),
         "confidence": round(float(probs[i]) * 100.0, 1)}
        for r, i in enumerate(order)
    ]
    best = int(order[0])
    return str(clf.classes_[best]), round(float(probs[best]) * 100.0, 1), alts


def load_t2_hybrid_assets(models_dir: Path | str = DEFAULT_MODELS) -> dict[str, Any]:
    """Load both Task 1 cascade (L1-L3) and Task 2 L4 artifacts."""
    models_dir = Path(models_dir)
    assets = {
        "t1_cascade": load_cascade_assets(models_dir),
        "l4":         joblib.load(models_dir / T2_L4_SEG),
        "seg_vec":    joblib.load(models_dir / T2_L4_SEG_VEC),
        "summary":    {},
    }
    summary_path = models_dir / T2_SUMMARY
    if summary_path.exists():
        assets["summary"] = json.loads(summary_path.read_text(encoding="utf-8"))
    return assets


def cascade_predict_t2(
    segment_text: str,
    full_text: str,
    assets: dict[str, Any],
    top_n: int = 3,
) -> dict[str, Any]:
    """
    Predict sub-industry code for a company segment.

    Parameters
    ----------
    segment_text : SegmentName + SegmentDescription (used by L4)
    full_text    : LongProfile + SegmentName + SegmentDescription (used by T1 cascade)
                   Pass the same as segment_text if LongProfile is not available.
    assets       : loaded from load_t2_hybrid_assets()
    top_n        : number of alternatives to return per level
    """
    t1 = assets["t1_cascade"]

    # ── Stage 1: Task 1 cascade -> MSTAR code ─────────────────────────────────
    X_full = t1["vectorizer"].transform([full_text])

    sector, sector_conf, sector_alts = _rank_artifact(t1["l1"], X_full, top_n=top_n)

    l2_art = t1["l2"].get(sector)
    if l2_art is None:
        raise KeyError(f"No T1 L2 artifact for sector '{sector}'")
    group, group_conf, group_alts = _rank_artifact(l2_art, X_full, top_n=top_n)

    l3_art = t1["l3"].get(group)
    if l3_art is None:
        raise KeyError(f"No T1 L3 artifact for group '{group}'")
    mstar, mstar_conf, mstar_alts = _rank_artifact(l3_art, X_full, top_n=top_n)

    # ── Stage 2: L4 -> sub-industry within predicted MSTAR ────────────────────
    X_seg = assets["seg_vec"].transform([segment_text])
    l4_art = assets["l4"].get(mstar)
    if l4_art is None:
        raise KeyError(f"No T2 L4 artifact for MSTAR '{mstar}' — "
                       f"MSTAR prediction may be outside training distribution")

    sub, sub_conf, sub_alts = _rank_l4(l4_art, X_seg, top_n=top_n)

    return {
        "sub_code":    sub,
        "mstar_code":  mstar,
        "group_code":  group,
        "sector_code": sector,
        "confidence":  round(min(sector_conf, group_conf, mstar_conf, sub_conf), 1),
        "confidence_path": {
            "sector": sector_conf,
            "group":  group_conf,
            "mstar":  mstar_conf,
            "sub":    sub_conf,
        },
        "alternatives": {
            "sector": sector_alts,
            "group":  group_alts,
            "mstar":  mstar_alts,
            "sub":    sub_alts,
        },
    }
