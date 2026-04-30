"""
Hugging Face Spaces — GECS DeBERTa-v3 Classifier
Exposes a Gradio UI + a /api/predict_llm REST endpoint consumed by the
Next.js frontend on Vercel via a server-side proxy.

Required HF Space secrets (Settings → Variables and secrets):
  HF_MODEL_REPO   — e.g. "Akash-AG/gecs-deberta-v3"  (default used if unset)
  HF_API_SECRET   — shared secret that the Vercel proxy must send as
                    the X-API-Secret header to authenticate requests
"""
import os, json, asyncio
import torch
import gradio as gr
from fastapi import Request
from fastapi.responses import JSONResponse
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# ── Label maps ────────────────────────────────────────────────────────────────
MSTAR_LABELS = {
    "10320010": "Capital Markets",        "10320020": "Regional Banks",
    "10320030": "Diversified Banks",      "10320040": "Insurance — Life & Health",
    "10320050": "Insurance — P&C",        "10340010": "Asset Management",
    "30820010": "Internet Content",       "30820020": "Software — Application",
    "30820030": "Software — Infrastructure", "30830010": "Internet Search & AI",
    "31130010": "Semiconductors",         "31130020": "Semiconductor Equipment",
    "20527020": "Biotechnology",          "20527010": "Drug Manufacturers — General",
    "20528010": "Medical Devices",        "20524010": "Healthcare Plans",
    "21022020": "Specialty Retail",       "21021010": "Discount Stores",
    "31020010": "Aerospace & Defense",    "31020020": "Industrial Machinery",
    "10110010": "Oil & Gas Integrated",   "10110020": "Oil & Gas E&P",
    "10110030": "Oil & Gas Midstream",    "30610010": "REIT — Retail",
    "30610020": "REIT — Office",          "31110030": "IT Services & Cloud",
    "20650010": "Medical Equipment",      "30910020": "Oil & Gas Equipment",
    "30810030": "Telecom Services",       "30830020": "Entertainment",
}

PREFIX_LABELS = {
    "101": "Energy & Extraction",    "102": "Basic Materials & Consumer",
    "103": "Financial Services",     "104": "Real Estate / Construction",
    "205": "Healthcare & Pharma",    "206": "Medical Equipment",
    "207": "Healthcare Services",    "210": "Consumer Retail",
    "306": "Real Estate (REIT)",     "308": "Technology & Communications",
    "309": "Energy Equipment",       "310": "Industrials & Manufacturing",
    "311": "IT & Semiconductors",
}

# ── Security ──────────────────────────────────────────────────────────────────
# Must match the HF_API_SECRET set on Vercel and in the HF Space secrets.
HF_API_SECRET = os.environ.get("HF_API_SECRET", "")

# ── Model loading ─────────────────────────────────────────────────────────────
device = "cuda" if torch.cuda.is_available() else "cpu"
HF_MODEL_REPO = os.environ.get("HF_MODEL_REPO", "Akash-AG/gecs-deberta-v3")
HF_TOKEN      = os.environ.get("HF_TOKEN", None)
JSON_MAP      = "task1_idx_to_code.json"

print(f"Loading DeBERTa from {HF_MODEL_REPO} on {device.upper()}...")
MODELS_READY = False
try:
    from transformers import DebertaV2Tokenizer
    tokenizer = DebertaV2Tokenizer.from_pretrained(HF_MODEL_REPO, token=HF_TOKEN)
    model     = AutoModelForSequenceClassification.from_pretrained(HF_MODEL_REPO, token=HF_TOKEN)
    model.to(device).eval()
    with open(JSON_MAP) as f:
        idx_to_code = {int(k): str(v) for k, v in json.load(f).items()}
    MODELS_READY = True
    print("Model loaded ✓")
except Exception as e:
    print(f"ERROR loading model: {e}")

# ── Inference helpers ─────────────────────────────────────────────────────────
def _get_label(code: str) -> str:
    direct = MSTAR_LABELS.get(code)
    if direct:
        return direct
    broad = PREFIX_LABELS.get(code[:3], "Miscellaneous Industry")
    return f"{broad} (Code: {code})"

def _run_inference(text: str):
    inputs = tokenizer(
        [text], truncation=True, padding="max_length",
        max_length=512, return_tensors="pt"
    )
    inputs = {k: v.to(device) for k, v in inputs.items()}
    with torch.no_grad():
        idx = model(**inputs).logits.argmax(dim=-1).item()
    code = idx_to_code.get(idx, "Unknown")
    return code, _get_label(code)

# ── Gradio UI ─────────────────────────────────────────────────────────────────
def gradio_predict(text: str):
    if not MODELS_READY:
        return "Model offline — see Space logs.", ""
    if not text.strip():
        return "Please enter a company description.", ""
    code, label = _run_inference(text)
    return f"**{label}**", f"`{code}`"

with gr.Blocks(title="GECS DeBERTa Classifier", theme=gr.themes.Base()) as demo:
    gr.Markdown("## GECS DeBERTa-v3 Industry Classifier\nMGT 599 Capstone · Task 1 · 29 Classes")
    with gr.Row():
        inp = gr.Textbox(label="Company Description", lines=5,
                         placeholder="The company provides retail banking...")
    with gr.Row():
        label_out = gr.Markdown(label="Predicted Industry")
        code_out  = gr.Textbox(label="MSTAR Code")
    btn = gr.Button("Classify →", variant="primary")
    btn.click(gradio_predict, inputs=inp, outputs=[label_out, code_out])

# ── Launch and attach custom REST routes ─────────────────────────────────────
fastapi_app, _, _ = demo.launch(
    server_name="0.0.0.0",
    server_port=7860,
    prevent_thread_lock=True,
)

@fastapi_app.post("/api/predict_llm")
async def predict_llm_endpoint(request: Request):
    # ── Auth check ────────────────────────────────────────────────────────────
    if HF_API_SECRET:
        incoming = request.headers.get("X-API-Secret", "")
        if incoming != HF_API_SECRET:
            return JSONResponse({"error": "Unauthorized"}, status_code=401)

    if not MODELS_READY:
        return JSONResponse(
            {"error": "DeBERTa model offline. Check Space logs."}, status_code=503
        )

    body     = await request.json()
    raw_text = body.get("text", "").strip()
    if not raw_text:
        return JSONResponse({"error": "Empty text provided."}, status_code=400)

    try:
        code, label = _run_inference(raw_text)
        return JSONResponse({
            "success":     True,
            "mstar_code":  code,
            "mstar_label": label,
            "sub_code":    "N/A (LLM Task 1 Only)",
            "sub_label":   "N/A",
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

asyncio.get_event_loop().run_forever()
