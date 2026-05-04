from __future__ import annotations

from flask import Flask, jsonify, request
from flask_cors import CORS

from legendary.explanations import generate_explanation
from legendary.inference_router import RouterThresholds, route_prediction
from legendary.shared import get_label
from legendary.taxonomy_crosswalk import get_cross_taxonomy, load_crosswalk
from scripts.cascade_predict import load_cascade_assets


app = Flask(__name__)
CORS(app)


try:
    CASCADE_ASSETS = load_cascade_assets()
    CASCADE_READY = True
    CASCADE_ERROR = None
except Exception as exc:
    CASCADE_ASSETS = None
    CASCADE_READY = False
    CASCADE_ERROR = str(exc)

# DeBERTa is intentionally skipped — cascade SVM scores 88.90% vs DeBERTa's 64%.
# Passing None tells the router to use cascade-only, which returns in <100ms.
DEBERTA = None
CROSSWALK = load_crosswalk()
THRESHOLDS = RouterThresholds(high_confidence=85.0, medium_confidence=60.0)


def _build_legendary_response(text: str) -> dict:
    route = route_prediction(
        text=text,
        cascade_assets=CASCADE_ASSETS,
        deberta_predictor=DEBERTA,
        thresholds=THRESHOLDS,
    )
    code = route["mstar_code"]
    label = route.get("mstar_label") or get_label(code)
    explanation = generate_explanation(text, label, code, route["engine"])
    taxonomy_map = get_cross_taxonomy(code, CROSSWALK)

    return {
        "success": True,
        "engine": route["engine"],
        "route_reason": route["route_reason"],
        "mstar_code": code,
        "mstar_label": label,
        "confidence": route["confidence"],
        "alternatives": route.get("alternatives", []),
        "cascade": route.get("cascade"),
        "deberta": route.get("deberta"),
        "explanation": explanation["text"],
        "explanation_engine": explanation["engine"],
        "taxonomy_map": taxonomy_map,
    }


@app.get("/")
def root():
    return "Legendary roadmap server online", 200


@app.get("/health")
def health():
    return jsonify(
        {
            "ok": CASCADE_READY,
            "cascade_ready": CASCADE_READY,
            "cascade_error": CASCADE_ERROR,
            "deberta_ready": False,
            "deberta_note": "DeBERTa skipped — cascade SVM is the champion (88.90% F1).",
            "crosswalk_entries": len(CROSSWALK),
        }
    ), (200 if CASCADE_READY else 503)


@app.post("/api/predict_routed")
def predict_routed():
    if not CASCADE_READY:
        return jsonify({"error": "Cascade assets are offline.", "details": CASCADE_ERROR}), 503

    payload = request.get_json(silent=True) or {}
    text = str(payload.get("text", "")).strip()
    if not text:
        return jsonify({"error": "Empty text provided."}), 400

    response = _build_legendary_response(text)
    return jsonify(response)


@app.post("/api/explain_prediction")
def explain_prediction():
    payload = request.get_json(silent=True) or {}
    text = str(payload.get("text", "")).strip()
    code = str(payload.get("mstar_code", "")).strip()
    label = str(payload.get("mstar_label", "")).strip() or get_label(code)
    engine = str(payload.get("engine", "Unknown")).strip() or "Unknown"

    if not text or not code:
        return jsonify({"error": "Both text and mstar_code are required."}), 400

    explanation = generate_explanation(text, label, code, engine)
    return jsonify({"success": True, "explanation": explanation["text"], "engine": explanation["engine"]})


@app.post("/api/predict_legendary")
def predict_legendary():
    if not CASCADE_READY:
        return jsonify({"error": "Cascade assets are offline.", "details": CASCADE_ERROR}), 503

    payload = request.get_json(silent=True) or {}
    text = str(payload.get("text", "")).strip()
    if not text:
        return jsonify({"error": "Empty text provided."}), 400

    response = _build_legendary_response(text)
    return jsonify(response)


if __name__ == "__main__":
    from waitress import serve
    print("Legendary server starting on http://localhost:5003")
    serve(app, host="0.0.0.0", port=5003)
