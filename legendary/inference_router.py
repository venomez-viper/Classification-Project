from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from legendary.shared import get_label
from scripts.cascade_predict import cascade_predict


@dataclass(frozen=True)
class RouterThresholds:
    high_confidence: float = 85.0
    medium_confidence: float = 60.0


def _normalize_cascade_alts(raw_alts: list[dict]) -> list[dict]:
    """Convert cascade code-level alternatives to unified format with code + label fields."""
    result = []
    for alt in raw_alts:
        code = alt["label"]  # at Level 3 the label field IS the mstar code string
        result.append({
            "rank": alt["rank"],
            "code": code,
            "label": get_label(code),
            "confidence": alt["confidence"],
        })
    return result


def route_prediction(
    text: str,
    cascade_assets: dict[str, Any],
    deberta_predictor=None,
    thresholds: RouterThresholds = RouterThresholds(),
) -> dict[str, Any]:
    cascade_result = cascade_predict(text, cascade_assets, top_n=3)
    cascade_code = cascade_result["mstar_code"]
    cascade_conf = float(cascade_result["confidence"])
    cascade_label = get_label(cascade_code)                          # Bug 2 fix
    normalized_alts = _normalize_cascade_alts(                       # Bug 3 fix
        cascade_result["alternatives"]["code"]
    )

    if cascade_conf >= thresholds.high_confidence:
        return {
            "engine": "SVM Cascade",
            "route_reason": f"Cascade confidence {cascade_conf:.1f}% met the high-confidence threshold.",
            "mstar_code": cascade_code,
            "mstar_label": cascade_label,
            "confidence": cascade_conf,
            "cascade": cascade_result,
            "alternatives": normalized_alts,
        }

    if deberta_predictor is not None and getattr(deberta_predictor, "ready", False):
        deberta_result = deberta_predictor.predict(text, top_n=3)
        deberta_conf = float(deberta_result["confidence"])

        if deberta_conf >= thresholds.medium_confidence:
            return {
                "engine": "DeBERTa",
                "route_reason": (
                    f"Cascade confidence {cascade_conf:.1f}% was below {thresholds.high_confidence:.1f}%, "
                    f"so the request escalated to DeBERTa, which responded at {deberta_conf:.1f}%."
                ),
                "mstar_code": deberta_result["mstar_code"],
                "mstar_label": deberta_result["mstar_label"],
                "confidence": deberta_conf,
                "cascade": cascade_result,
                "deberta": deberta_result,
                "alternatives": deberta_result["alternatives"],
            }

        # Both models below threshold — check if they agree
        models_agree = cascade_code == deberta_result["mstar_code"]

        if deberta_conf >= cascade_conf:
            best_code = deberta_result["mstar_code"]
            best_label = deberta_result["mstar_label"]
            best_alts = deberta_result["alternatives"]
        else:
            best_code = cascade_code
            best_label = cascade_label
            best_alts = normalized_alts

        if models_agree:
            engine_label = "Consensus"
            reason = (
                f"Cascade ({cascade_conf:.1f}%) and DeBERTa ({deberta_conf:.1f}%) both fell below the "
                f"individual confidence threshold, but both independently predicted {best_label} — "
                "agreement between models validates the result."
            )
        else:
            engine_label = "Low Confidence"
            reason = (
                f"Cascade confidence {cascade_conf:.1f}% and DeBERTa confidence {deberta_conf:.1f}% "
                "both fell below threshold — returning the higher-confidence result."
            )

        return {
            "engine": engine_label,
            "route_reason": reason,
            "mstar_code": best_code,
            "mstar_label": best_label,
            "confidence": max(cascade_conf, deberta_conf),
            "cascade": cascade_result,
            "deberta": deberta_result,
            "alternatives": best_alts,
        }

    return {
        "engine": "SVM Cascade",
        "route_reason": (
            f"Cascade confidence {cascade_conf:.1f}% did not meet the ideal threshold, but DeBERTa is "
            "offline, so the cascade result was served as the safest available prediction."
        ),
        "mstar_code": cascade_code,
        "mstar_label": cascade_label,
        "confidence": cascade_conf,
        "cascade": cascade_result,
        "alternatives": normalized_alts,
    }
