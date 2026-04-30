import os
import joblib
import numpy as np
import pandas as pd
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

from breezeml import load, predict

app = Flask(__name__)
CORS(app)

# ── GECS Human-Readable Label Lookup ───────────────────────────────────────────
MSTAR_LABELS = {
    "10320010": "Capital Markets",
    "10320020": "Regional Banks",
    "10320030": "Diversified Banks",
    "10320040": "Insurance — Life & Health",
    "10320050": "Insurance — Property & Casualty",
    "10340010": "Asset Management",
    "10340060": "Insurance — Multi-line",
    "10310010": "Diversified Financial Services",
    "30820010": "Internet Content & Information",
    "30820020": "Software — Application",
    "30820030": "Software — Infrastructure",
    "30830010": "Internet Search & AI Services",
    "31130010": "Semiconductors",
    "31130020": "Semiconductor Equipment",
    "31120060": "Scientific & Technical Instruments",
    "30810010": "Electronic Components",
    "30810020": "Electronic Manufacturing Services",
    "20527020": "Biotechnology",
    "20527010": "Drug Manufacturers — General",
    "20527050": "Drug Manufacturers — Specialty & Generic",
    "20528010": "Medical Devices",
    "20528020": "Medical Instruments & Supplies",
    "20524010": "Healthcare Plans",
    "20525010": "Medical Care Facilities",
    "20525040": "Packaged Foods",
    "21022020": "Specialty Retail",
    "21021010": "Discount Stores",
    "21022030": "Department Stores",
    "21012010": "Apparel Manufacturing",
    "21012020": "Footwear & Accessories",
    "20529010": "Consumer Electronics",
    "31020010": "Aerospace & Defense",
    "31020020": "Industrial Machinery",
    "31020030": "Diversified Industrials",
    "10310020": "Engineering & Construction",
    "31120020": "Electrical Equipment & Parts",
    "10110010": "Oil & Gas Integrated",
    "10110020": "Oil & Gas E&P",
    "10110030": "Oil & Gas Midstream",
    "10130020": "Agricultural Inputs",
    "10310015": "Diversified Chemicals",
    "30610010": "REIT — Retail",
    "30610020": "REIT — Office",
    "30610030": "REIT — Industrial",
    "30610040": "REIT — Healthcare",
    "30620010": "Real Estate Services",
    "30810030": "Telecom Services",
    "30830020": "Entertainment",
    "30830030": "Broadcasting & Media",
    "31110030": "IT Services & Cloud Computing",
    "20650010": "Medical Equipment & Instruments",
    "30910020": "Oil & Gas Equipment & Services",
}

SUBINDUSTRY_LABELS = {
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

def get_label(code, lookup):
    return lookup.get(str(code), None)


# ── Confidence helpers ──────────────────────────────────────────────────────────

def _softmax(x):
    x = np.array(x, dtype=np.float64)
    x -= x.max()
    e = np.exp(x)
    return e / e.sum()

def _unwrap(model):
    """Return the raw sklearn estimator from a breezeml wrapper (tries common attrs)."""
    for attr in [None, "model", "_clf", "_estimator", "estimator"]:
        obj = model if attr is None else getattr(model, attr, None)
        if obj is not None and hasattr(obj, "decision_function") and hasattr(obj, "classes_"):
            return obj
    return None

def extract_confidence(model, X_sparse, label_lookup, n=3):
    """
    Uses LinearSVC.decision_function → softmax to produce pseudo-probabilities.
    Returns (top_confidence_pct, list_of_alternatives).
    """
    try:
        clf = _unwrap(model)
        if clf is None:
            return None, []
        scores = clf.decision_function(X_sparse)   # (1, n_classes)
        probs  = _softmax(scores[0])
        top_i  = np.argsort(probs)[::-1][:n]
        alts = [
            {
                "rank":       int(rank) + 1,
                "code":       str(clf.classes_[i]),
                "label":      label_lookup.get(str(clf.classes_[i]), f"Code {clf.classes_[i]}"),
                "confidence": round(float(probs[i]) * 100, 1),
            }
            for rank, i in enumerate(top_i)
        ]
        return round(float(probs[top_i[0]]) * 100, 1), alts
    except Exception:
        return None, []

def extract_top_features(model, vec, X_sparse, n=6):
    """
    Returns the top TF-IDF term names that contributed most to the predicted class.
    Uses LinearSVC.coef_ × tfidf_value as contribution score.
    """
    try:
        clf = _unwrap(model)
        if clf is None or not hasattr(clf, "coef_"):
            return []
        scores      = clf.decision_function(X_sparse)
        pred_idx    = int(np.argmax(scores[0]))
        coef        = clf.coef_[pred_idx]
        tfidf_vals  = np.asarray(X_sparse.todense())[0]
        contrib     = coef * tfidf_vals
        top_i       = np.argsort(contrib)[::-1][:n]
        names       = vec.get_feature_names_out()
        return [str(names[i]) for i in top_i if contrib[i] > 0]
    except Exception:
        return []


# ── Model Loading ───────────────────────────────────────────────────────────────
print("Loading breezeml inference pipeline...")
try:
    model1 = load("models/task1_svm_model.joblib")
    vec1   = joblib.load("models/task1_tfidf_vectorizer.pkl")
    model2 = load("models/task2_svc_model.joblib")
    vec2   = joblib.load("models/task2_tfidf_vectorizer.pkl")
    print("System check: Models mounted successfully.")
    MODELS_READY = True
except Exception as e:
    print(f"System Error: Failed to load models. Details: {e}")
    MODELS_READY = False


@app.errorhandler(Exception)
def handle_exception(e):
    return jsonify({"error": str(e)}), 500


@app.route("/", methods=["GET"])
def serve_frontend():
    return render_template("index.html")


@app.route("/api/predict", methods=["POST"])
def execute_prediction():
    if not MODELS_READY:
        return jsonify({"error": "Models offline. Please train notebooks first."}), 503

    data     = request.get_json(silent=True) or {}
    raw_text = data.get("text", "")

    if not raw_text.strip():
        return jsonify({"error": "Empty text provided."}), 400

    try:
        X1  = vec1.transform([raw_text])
        df1 = pd.DataFrame(X1.toarray(), columns=vec1.get_feature_names_out())
        X2  = vec2.transform([raw_text])
        df2 = pd.DataFrame(X2.toarray(), columns=vec2.get_feature_names_out())

        pred_mstar       = predict(model1, df1)
        pred_subindustry = predict(model2, df2)

        mstar_code  = str(pred_mstar[0])
        sub_code    = str(pred_subindustry[0])
        mstar_label = get_label(mstar_code, MSTAR_LABELS) or "Unrecognised Category"
        sub_label   = get_label(sub_code, SUBINDUSTRY_LABELS) or "Granular Activity Code"

        conf1, alts1 = extract_confidence(model1, X1, MSTAR_LABELS)
        conf2, alts2 = extract_confidence(model2, X2, SUBINDUSTRY_LABELS)
        feat1        = extract_top_features(model1, vec1, X1)
        feat2        = extract_top_features(model2, vec2, X2)

        return jsonify({
            "success":        True,
            "mstar_code":     mstar_code,
            "mstar_label":    mstar_label,
            "sub_code":       sub_code,
            "sub_label":      sub_label,
            "confidence_t1":  conf1,
            "alternatives_t1": alts1,
            "features_t1":    feat1,
            "confidence_t2":  conf2,
            "alternatives_t2": alts2,
            "features_t2":    feat2,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
