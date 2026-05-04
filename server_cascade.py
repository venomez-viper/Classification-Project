from __future__ import annotations

import sys
from pathlib import Path

from flask import Flask, jsonify, request
from flask_cors import CORS

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.cascade_predict import cascade_predict, load_cascade_assets


app = Flask(__name__)
CORS(app)


MSTAR_LABELS = {
    "10110010": "Oil & Gas Integrated",
    "10110020": "Oil & Gas E&P",
    "10110030": "Oil & Gas Midstream",
    "10310010": "Diversified Financial Services",
    "10320010": "Capital Markets",
    "10320020": "Regional Banks",
    "10320030": "Diversified Banks",
    "10320040": "Insurance - Life & Health",
    "10320050": "Insurance - Property & Casualty",
    "10340010": "Asset Management",
    "10340060": "Insurance - Multi-line",
    "20524010": "Healthcare Plans",
    "20525010": "Medical Care Facilities",
    "20527010": "Drug Manufacturers - General",
    "20527020": "Biotechnology",
    "20527050": "Drug Manufacturers - Specialty & Generic",
    "20528010": "Medical Devices",
    "20528020": "Medical Instruments & Supplies",
    "20650010": "Medical Equipment & Instruments",
    "30810010": "Electronic Components",
    "30810020": "Electronic Manufacturing Services",
    "30820010": "Internet Content & Information",
    "30820020": "Software - Application",
    "30820030": "Software - Infrastructure",
    "30830010": "Internet Search & AI Services",
    "30830020": "Entertainment",
    "30830030": "Broadcasting & Media",
    "30910020": "Oil & Gas Equipment & Services",
    "31020010": "Aerospace & Defense",
    "31020020": "Industrial Machinery",
    "31020030": "Diversified Industrials",
    "31110030": "IT Services & Cloud Computing",
    "31120020": "Electrical Equipment & Parts",
    "31120060": "Scientific & Technical Instruments",
    "31130010": "Semiconductors",
    "31130020": "Semiconductor Equipment",
}


try:
    CASCADE_ASSETS = load_cascade_assets()
    CASCADE_READY = True
except Exception as exc:
    CASCADE_ASSETS = None
    CASCADE_READY = False
    CASCADE_ERROR = str(exc)


@app.get("/")
def root() -> tuple[str, int]:
    if CASCADE_READY:
        return "Cascade server online", 200
    return "Cascade server offline", 503


@app.get("/health")
def health():
    if CASCADE_READY:
        return jsonify({"ok": True, "engine": "cascade_svm"})
    return jsonify({"ok": False, "error": CASCADE_ERROR}), 503


@app.post("/api/predict_cascade")
def predict_cascade():
    if not CASCADE_READY:
        return (
            jsonify(
                {
                    "error": "Cascade artifacts not found. Run `python scripts/train_cascade.py` first.",
                    "details": CASCADE_ERROR,
                }
            ),
            503,
        )

    payload = request.get_json(silent=True) or {}
    raw_text = str(payload.get("text", "")).strip()
    if not raw_text:
        return jsonify({"error": "Empty text provided."}), 400

    result = cascade_predict(raw_text, CASCADE_ASSETS, top_n=3)
    mstar_code = result["mstar_code"]
    mstar_label = MSTAR_LABELS.get(mstar_code, f"Code {mstar_code}")

    return jsonify(
        {
            "success": True,
            "engine": "cascade_svm",
            "sector_code": result["sector_code"],
            "group_code": result["group_code"],
            "mstar_code": mstar_code,
            "mstar_label": mstar_label,
            "confidence": result["confidence"],
            "confidence_path": result["confidence_path"],
            "alternatives": result["alternatives"],
        }
    )


if __name__ == "__main__":
    app.run(debug=True, port=5002)
