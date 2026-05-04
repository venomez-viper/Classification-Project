import os
import sys
import json
import torch
from flask import Flask, request, jsonify
from flask_cors import CORS
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# Make the project root importable so we can share label lookups
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from legendary.shared import get_label  # noqa: E402

app = Flask(__name__)
CORS(app)


# ── Load models ───────────────────────────────────────────────────────────────
device = "cuda" if torch.cuda.is_available() else "cpu"
RESULTS_DIR    = "llm_finetuning/results"
TOKENIZER_PATH = "microsoft/deberta-v3-small"  # local cache

print("=" * 55)
print(f"DeBERTa server — device: {device.upper()}")
print("=" * 55)


def _load_model(task: str):
    model_dir = os.path.join(RESULTS_DIR, f"{task}_best_model")
    idx_map   = os.path.join("llm_finetuning", "data", f"{task}_idx_to_code.json")
    try:
        tok = AutoTokenizer.from_pretrained(model_dir, local_files_only=True)
        mdl = AutoModelForSequenceClassification.from_pretrained(model_dir, local_files_only=True)
        mdl.to(device)
        mdl.eval()
        with open(idx_map, "r") as f:
            code_map = {int(k): str(v) for k, v in json.load(f).items()}
        print(f"  ✓ {task} model loaded  ({len(code_map)} classes)")
        return tok, mdl, code_map, True, None
    except Exception as exc:
        print(f"  ✗ {task} model NOT loaded: {exc}")
        return None, None, None, False, str(exc)


T1_TOK, T1_MDL, T1_MAP, T1_READY, T1_ERR = _load_model("task1")
T2_TOK, T2_MDL, T2_MAP, T2_READY, T2_ERR = _load_model("task2")

print("=" * 55)
if not T1_READY:
    print("WARNING: Task-1 model unavailable. Train with:")
    print("  python llm_finetuning/scripts/train_local.py --task task1")
if not T2_READY:
    print("Task-2 model not found. Train with:")
    print("  python llm_finetuning/scripts/train_local.py --task task2")
print("=" * 55)


# ── Inference helper ──────────────────────────────────────────────────────────
def _predict(text: str, tok, mdl, code_map: dict, top_n: int = 3) -> dict:
    inputs = tok(
        [text],
        truncation=True,
        padding="max_length",
        max_length=128,
        return_tensors="pt",
    )
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        logits = mdl(**inputs).logits[0]
        probs  = torch.softmax(logits, dim=-1)
        top_v, top_i = torch.topk(probs, k=min(top_n, probs.shape[0]))

    best_code  = code_map.get(int(top_i[0].item()), "Unknown")
    confidence = round(float(top_v[0].item()) * 100.0, 1)

    alternatives = []
    for rank, (prob, idx) in enumerate(zip(top_v.tolist(), top_i.tolist()), start=1):
        code = code_map.get(int(idx), "Unknown")
        alternatives.append({
            "rank":       rank,
            "code":       code,
            "label":      get_label(code),
            "confidence": round(float(prob) * 100.0, 1),
        })

    return {
        "code":         best_code,
        "label":        get_label(best_code),
        "confidence":   confidence,
        "alternatives": alternatives,
    }


# ── Routes ────────────────────────────────────────────────────────────────────
@app.errorhandler(Exception)
def handle_exception(e):
    return jsonify({"error": str(e)}), 500


@app.route("/health")
def health():
    return jsonify({
        "task1_ready": T1_READY, "task1_error": T1_ERR,
        "task2_ready": T2_READY, "task2_error": T2_ERR,
        "device":      device,
    })


@app.route("/api/predict_llm", methods=["POST"])
def predict_llm():
    if not T1_READY:
        return jsonify({"error": "Task-1 DeBERTa model not loaded.", "details": T1_ERR}), 503

    data     = request.get_json(silent=True) or {}
    raw_text = data.get("text", "").strip()
    if not raw_text:
        return jsonify({"error": "Empty text provided."}), 400

    t1 = _predict(raw_text, T1_TOK, T1_MDL, T1_MAP)

    response = {
        "success":      True,
        "engine":       "DeBERTa-v3-small",
        "mstar_code":   t1["code"],
        "mstar_label":  t1["label"],
        "confidence":   t1["confidence"],
        "alternatives": t1["alternatives"],
        "task2_ready":  T2_READY,
    }

    if T2_READY:
        t2 = _predict(raw_text, T2_TOK, T2_MDL, T2_MAP)
        response["sub_code"]         = t2["code"]
        response["sub_label"]        = t2["label"]
        response["sub_confidence"]   = t2["confidence"]
        response["sub_alternatives"] = t2["alternatives"]

    return jsonify(response)


if __name__ == "__main__":
    from waitress import serve
    print("DeBERTa server starting on http://localhost:5001")
    serve(app, host="0.0.0.0", port=5001)
