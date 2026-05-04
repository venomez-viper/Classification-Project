"""
GECS Industry Classification Server
=====================================
Serves the main web UI + /api/predict endpoint.

Models:
  Task 1  — 3-level cascade SVM (Sector->Group->MSTAR)   88.90% Macro F1 / 145 classes
  Task 2  — 4-level hybrid cascade (T1→MSTAR + L4 SVM)  55.41% Macro F1 / 428 classes

Run locally:
  python server.py          → http://localhost:5000
"""
import json
import os
import sys
from pathlib import Path

import numpy as np
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.cascade_predict import (
    load_cascade_assets,
    cascade_predict,
    _rank_artifact,
)
from scripts.cascade_predict_t2 import load_t2_hybrid_assets, cascade_predict_t2

app = Flask(__name__)
CORS(app)


# ── Label lookups ────────────────────────────────────────────���─────────────────

# Task 1 — curated MSTAR industry labels
MSTAR_LABELS = {
    "10110010": "Oil & Gas Integrated",         "10110020": "Oil & Gas E&P",
    "10110030": "Oil & Gas Midstream",           "10120010": "Coal & Consumable Fuels",
    "10130010": "Agricultural Inputs",           "10130020": "Agricultural Inputs",
    "10140010": "Aluminum",                      "10140020": "Copper",
    "10200010": "Chemicals — Specialty",         "10200020": "Chemicals — Commodity",
    "10200030": "Diversified Chemicals",         "10310010": "Diversified Financial Services",
    "10320010": "Capital Markets",               "10320020": "Regional Banks",
    "10320030": "Diversified Banks",             "10320040": "Insurance — Life & Health",
    "10320050": "Insurance — Property & Casualty","10340010": "Asset Management",
    "10340060": "Insurance — Multi-line",        "20524010": "Healthcare Plans",
    "20525010": "Medical Care Facilities",       "20527010": "Drug Manufacturers — General",
    "20527020": "Biotechnology",                 "20527050": "Drug Manufacturers — Specialty",
    "20528010": "Medical Devices",               "20528020": "Medical Instruments & Supplies",
    "20529010": "Consumer Electronics",          "20650010": "Medical Equipment & Instruments",
    "21012010": "Apparel Manufacturing",         "21012020": "Footwear & Accessories",
    "21021010": "Discount Stores",               "21022020": "Specialty Retail",
    "21022030": "Department Stores",             "30610010": "REIT — Retail",
    "30610020": "REIT — Office",                 "30610030": "REIT — Industrial",
    "30610040": "REIT — Healthcare",             "30620010": "Real Estate Services",
    "30810010": "Electronic Components",         "30810020": "Electronic Manufacturing Services",
    "30810030": "Telecom Services",              "30820010": "Internet Content & Information",
    "30820020": "Software — Application",        "30820030": "Software — Infrastructure",
    "30830010": "Internet Search & AI Services", "30830020": "Entertainment",
    "30830030": "Broadcasting & Media",          "30910020": "Oil & Gas Equipment & Services",
    "31020010": "Aerospace & Defense",           "31020020": "Industrial Machinery",
    "31020030": "Diversified Industrials",       "31110030": "IT Services & Cloud Computing",
    "31120020": "Electrical Equipment & Parts",  "31120060": "Scientific & Technical Instruments",
    "31130010": "Semiconductors",                "31130020": "Semiconductor Equipment",
}

# Task 2 — curated sub-industry labels (high-quality hand-curated entries)
SUBINDUSTRY_LABELS_CURATED = {
    "1032002001": "Retail Banking & Mortgage Lending",
    "1032002002": "Commercial & Corporate Banking",
    "1032001001": "Global Investment Banking",
    "1032001002": "Brokerage & Wealth Management",
    "3082002001": "Enterprise SaaS Platforms",
    "3082002002": "Developer Tools & Cloud Infrastructure",
    "3082001001": "Ad-Supported Web Platforms",
    "3082001002": "E-Commerce & Marketplace",
    "3083001001": "Search Engine & AI Services",
    "3113001001": "Logic Chips & Processors",
    "3113001002": "Memory & Storage Semiconductors",
    "2052702001": "Clinical-Stage Biopharmaceuticals",
    "2052701001": "Large-Cap Drug Manufacturing",
    "2052801001": "Surgical & Diagnostic Devices",
    "2052404001": "Managed Care & Health Plans",
    "2052504001": "Food Manufacturing — Packaged & Frozen",
    "3102001001": "Defense Systems & Aerospace Manufacturing",
    "3102002001": "Industrial Equipment Manufacturing",
    "1011001001": "Upstream Oil Exploration & Production",
    "1011003001": "Pipeline & Gas Transmission",
    "3111003005": "Cloud Platform & IT Infrastructure",
    "2065001001": "Surgical & Diagnostic Equipment",
    "3091006002": "Drilling & Oilfield Services",
}

# Supplement with training-data-derived labels for remaining 405 codes
_LABELS_JSON = ROOT / "models/sub_industry_labels.json"
_MSTAR_FULL_JSON = ROOT / "models/mstar_labels_full.json"

def _load_json_labels(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}

_sub_labels_ext  = _load_json_labels(_LABELS_JSON)
_mstar_labels_ext = _load_json_labels(_MSTAR_FULL_JSON)


def get_mstar_label(code: str) -> str:
    return (MSTAR_LABELS.get(str(code))
            or _mstar_labels_ext.get(str(code))
            or f"Industry Code {code}")

def get_sub_label(code: str) -> str:
    return (SUBINDUSTRY_LABELS_CURATED.get(code)
            or _sub_labels_ext.get(code)
            or f"Sub-industry {code}")


# ── Model loading ──────────────────────────────────────────────────────────────
print("Loading Task 1 cascade (Sector->Group->MSTAR, 88.90% F1)...")
try:
    T1_ASSETS = load_cascade_assets(ROOT / "models")
    T1_READY  = True
    print("  Task 1 cascade OK.")
except Exception as e:
    T1_ASSETS = None
    T1_READY  = False
    print(f"  Task 1 cascade FAILED: {e}")

print("Loading Task 2 hybrid cascade (T1->MSTAR + L4, 55.41% F1)...")
try:
    T2_ASSETS = load_t2_hybrid_assets(ROOT / "models")
    T2_READY  = True
    print("  Task 2 hybrid cascade OK.")
except Exception as e:
    T2_ASSETS = None
    T2_READY  = False
    print(f"  Task 2 hybrid cascade FAILED: {e}")

MODELS_READY = T1_READY


# ── Helpers ────────────────────────────────────────────────────────────────��───

def _softmax(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=np.float64)
    x -= x.max()
    e = np.exp(x)
    return e / e.sum()


def _extract_top_features(vec, X_sparse, model_artifact, n: int = 6) -> list[str]:
    """Return top TF-IDF term contributions for the predicted class (T1 final SVM)."""
    try:
        if model_artifact.get("type") != "svm":
            return []
        clf  = model_artifact["model"]
        sc   = clf.decision_function(X_sparse)
        idx  = int(np.argmax(sc[0] if np.ndim(sc) > 1 else sc))
        coef = clf.coef_[idx]
        vals = np.asarray(X_sparse.todense())[0]
        contrib = coef * vals
        top_i   = np.argsort(contrib)[::-1][:n]
        names   = vec.get_feature_names_out()
        return [str(names[i]) for i in top_i if contrib[i] > 0]
    except Exception:
        return []


@app.errorhandler(Exception)
def handle_exception(e):
    return jsonify({"error": str(e)}), 500


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route("/", methods=["GET"])
def serve_frontend():
    return render_template("index.html")


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "ok":        MODELS_READY,
        "t1_ready":  T1_READY,
        "t2_ready":  T2_READY,
        "t1_model":  "cascade_svm (88.90% Macro F1 / 145 classes)",
        "t2_model":  "hybrid_cascade (55.41% Macro F1 / 428 classes)",
    })


@app.route("/api/predict", methods=["POST"])
def execute_prediction():
    if not MODELS_READY:
        return jsonify({"error": "Models offline. Please run train_cascade.py and train_cascade_t2.py first."}), 503

    data     = request.get_json(silent=True) or {}
    raw_text = data.get("text", "").strip()
    if not raw_text:
        return jsonify({"error": "Empty text provided."}), 400

    try:
        # ── Task 1: 3-level cascade → MSTAR code ──────────────────────────────
        t1_result   = cascade_predict(raw_text, T1_ASSETS, top_n=3)
        mstar_code  = t1_result["mstar_code"]
        mstar_label = get_mstar_label(mstar_code)

        # Top features from the final L3 model
        X_vec    = T1_ASSETS["vectorizer"].transform([raw_text])
        sector   = t1_result["sector_code"]
        group    = t1_result["group_code"]
        l3_art   = T1_ASSETS["l3"].get(group)
        features_t1 = _extract_top_features(T1_ASSETS["vectorizer"], X_vec, l3_art) if l3_art else []

        # ── Task 2: hybrid cascade → sub-industry code ────────────────────────
        if T2_READY:
            try:
                t2_result = cascade_predict_t2(
                    segment_text=raw_text,
                    full_text=raw_text,
                    assets=T2_ASSETS,
                    top_n=3,
                )
                sub_code  = t2_result["sub_code"]
                sub_label = get_sub_label(sub_code)
                conf_t2   = t2_result["confidence"]
                alts_t2   = [
                    {**a, "label": get_sub_label(a["label"])}
                    for a in t2_result["alternatives"].get("sub", [])
                ]
                cascade_path_t2 = {
                    "sector": {"code": t2_result["sector_code"],
                               "conf": t2_result["confidence_path"]["sector"]},
                    "group":  {"code": t2_result["group_code"],
                               "conf": t2_result["confidence_path"]["group"]},
                    "mstar":  {"code": t2_result["mstar_code"],
                               "conf": t2_result["confidence_path"]["mstar"]},
                    "sub":    {"code": sub_code,
                               "conf": t2_result["confidence_path"]["sub"]},
                }
            except KeyError:
                # MSTAR not in T2 L4 training set — fall back to "Unknown"
                sub_code  = mstar_code
                sub_label = f"{mstar_label} (sub-industry N/A)"
                conf_t2   = t1_result["confidence"]
                alts_t2   = []
                cascade_path_t2 = None
        else:
            sub_code  = "N/A"
            sub_label = "Task 2 model offline"
            conf_t2   = None
            alts_t2   = []
            cascade_path_t2 = None

        return jsonify({
            "success":        True,
            # Task 1
            "mstar_code":     mstar_code,
            "mstar_label":    mstar_label,
            "confidence_t1":  t1_result["confidence"],
            "alternatives_t1": [
                {**a, "label": get_mstar_label(a["label"])}
                for a in t1_result["alternatives"].get("code", [])
            ],
            "cascade_path_t1": {
                "sector": {"code": t1_result["sector_code"],
                           "conf": t1_result["confidence_path"]["sector"]},
                "group":  {"code": t1_result["group_code"],
                           "conf": t1_result["confidence_path"]["group"]},
                "mstar":  {"code": mstar_code,
                           "conf": t1_result["confidence_path"]["code"]},
            },
            "features_t1":    features_t1,
            # Task 2
            "sub_code":       sub_code,
            "sub_label":      sub_label,
            "confidence_t2":  conf_t2,
            "alternatives_t2": alts_t2,
            "cascade_path_t2": cascade_path_t2,
            "features_t2":    [],
            # Meta
            "model_t1": "cascade_svm",
            "model_t2": "hybrid_cascade",
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    try:
        from waitress import serve
        print(f"Server starting on http://localhost:{port}")
        serve(app, host="0.0.0.0", port=port)
    except ImportError:
        print(f"Dev server starting on http://localhost:{port}")
        app.run(debug=True, port=port)
