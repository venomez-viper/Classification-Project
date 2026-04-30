import os
import json
import torch
from flask import Flask, request, jsonify
from flask_cors import CORS
from transformers import AutoTokenizer, AutoModelForSequenceClassification

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

PREFIX_LABELS = {
    "101": "Energy & Extraction",
    "102": "Basic Materials & Consumer",
    "103": "Financial Services",
    "104": "Real Estate / Construction",
    "205": "Healthcare & Pharma",
    "206": "Medical Equipment",
    "207": "Healthcare Services",
    "210": "Consumer Retail",
    "306": "Real Estate (REIT)",
    "308": "Technology & Communications",
    "309": "Energy Equipment",
    "310": "Industrials & Manufacturing",
    "311": "IT & Semiconductors",
}

def get_label(code, lookup):
    return lookup.get(str(code), None)

def get_fallback_label(code):
    prefix = str(code)[:3]
    broad_sector = PREFIX_LABELS.get(prefix, "Miscellaneous Industry")
    return f"{broad_sector} (Code: {code})"

# ── Load DeBERTa Model ────────────────────────────────────────────────────────
device = "cuda" if torch.cuda.is_available() else "cpu"
MODEL_PATH = "llm_finetuning/results/task1_best_model"
TOKENIZER_PATH = "microsoft/deberta-v3-small"
JSON_MAP = "llm_finetuning/data/task1_idx_to_code.json"

print("=" * 50)
print(f"Loading DeBERTa-v3 LLM on {device.upper()}...")
print("=" * 50)

MODELS_READY = False
try:
    tokenizer = AutoTokenizer.from_pretrained(TOKENIZER_PATH, local_files_only=True)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_PATH, local_files_only=True)
    model.to(device)
    model.eval()

    with open(JSON_MAP, "r") as f:
        idx_to_code = {int(k): str(v) for k, v in json.load(f).items()}

    print("Model mounted successfully. Ready for inference.")
    MODELS_READY = True
except Exception as e:
    print(f"ERROR loading model: {e}")
    print("Ensure you have run the training script and the model exists in llm_finetuning/results/")

@app.errorhandler(Exception)
def handle_exception(e):
    return jsonify({"error": str(e)}), 500

@app.route("/api/predict_llm", methods=["POST"])
def execute_llm_prediction():
    if not MODELS_READY:
        return jsonify({"error": "DeBERTa LLM offline. Please train the model first."}), 503

    data = request.get_json(silent=True) or {}
    raw_text = data.get("text", "")

    if not raw_text.strip():
        return jsonify({"error": "Empty text provided."}), 400

    try:
        # 1. Tokenize
        inputs = tokenizer(
            [raw_text], 
            truncation=True, 
            padding="max_length", 
            max_length=512, 
            return_tensors="pt"
        )
        inputs = {k: v.to(device) for k, v in inputs.items()}

        # 2. Forward Pass
        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits
            predicted_idx = logits.argmax(dim=-1).item()

        # 3. Map to Industry Code
        mstar_code = idx_to_code.get(predicted_idx, "Unknown")
        mstar_label = get_label(mstar_code, MSTAR_LABELS) or get_fallback_label(mstar_code)

        return jsonify({
            "success": True,
            "mstar_code": mstar_code,
            "mstar_label": mstar_label,
            # We didn't train task 2 for LLM, so we omit sub_code for the LLM UI
            "sub_code": "N/A (LLM Task 1 Only)",
            "sub_label": "N/A",
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5001)
