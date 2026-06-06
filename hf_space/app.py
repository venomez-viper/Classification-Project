"""
TAVSS — GECS Classifier (HF Space)
Serves:
  GET  /          — Gradio UI
  POST /api/predict           — REST JSON API (for Vercel frontend)
  POST /api/predict_legendary — same, alias kept for compatibility

Group 4 · MGT 599 Capstone · DePaul University
"""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import gradio as gr
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

MODELS_DIR = Path(__file__).resolve().parent / "models"

# ── Label maps — all 145 GECS industry codes (authoritative) ─────────────────
MSTAR_LABELS = {
    "10110010": "Agricultural Inputs",
    "10120010": "Building Materials",
    "10130010": "Chemicals",
    "10130020": "Specialty Chemicals",
    "10140010": "Lumber & Wood Production",
    "10140020": "Paper & Paper Products",
    "10150010": "Aluminum",
    "10150020": "Copper",
    "10150030": "Other Industrial Metals & Mining",
    "10150040": "Gold",
    "10150050": "Silver",
    "10150060": "Other Precious Metals & Mining",
    "10160010": "Coking Coal",
    "10160020": "Steel",
    "10200010": "Auto & Truck Dealerships",
    "10200020": "Auto Manufacturers",
    "10200030": "Auto Parts",
    "10200040": "Recreational Vehicles",
    "10220010": "Furnishings, Fixtures & Appliances",
    "10230010": "Homebuilding & Residential Construction",
    "10240010": "Textile Manufacturing",
    "10240020": "Apparel Manufacturing",
    "10240030": "Footwear & Accessories",
    "10250010": "Packaging & Containers",
    "10260010": "Personal Services",
    "10270010": "Restaurants",
    "10280010": "Apparel Retail",
    "10280020": "Department Stores",
    "10280030": "Home Improvement Retail",
    "10280040": "Luxury Goods",
    "10280050": "Internet Retail",
    "10280060": "Specialty Retail",
    "10290010": "Gambling",
    "10290020": "Leisure",
    "10290030": "Lodging",
    "10290040": "Resorts & Casinos",
    "10290050": "Travel Services",
    "10310010": "Asset Management",
    "10320010": "Banks — Diversified",
    "10320020": "Banks — Regional",
    "10320030": "Mortgage Finance",
    "10330010": "Capital Markets",
    "10330020": "Financial Data & Stock Exchanges",
    "10340010": "Insurance — Life",
    "10340020": "Insurance — Property & Casualty",
    "10340030": "Insurance — Reinsurance",
    "10340040": "Insurance — Specialty",
    "10340050": "Insurance — Brokers",
    "10340060": "Insurance — Diversified",
    "10350010": "Shell Companies",
    "10350020": "Financial Conglomerates",
    "10360010": "Credit Services",
    "10410010": "Real Estate — Development",
    "10410020": "Real Estate Services",
    "10410030": "Real Estate — Diversified",
    "10420010": "REIT — Healthcare Facilities",
    "10420020": "REIT — Hotel & Motel",
    "10420030": "REIT — Industrial",
    "10420040": "REIT — Office",
    "10420050": "REIT — Residential",
    "10420060": "REIT — Retail",
    "10420070": "REIT — Mortgage",
    "10420080": "REIT — Specialty",
    "10420090": "REIT — Diversified",
    "20510010": "Beverages — Brewers",
    "20510020": "Beverages — Wineries & Distilleries",
    "20520010": "Beverages — Non-Alcoholic",
    "20525010": "Confectioners",
    "20525020": "Farm Products",
    "20525030": "Household & Personal Products",
    "20525040": "Packaged Foods",
    "20540010": "Education & Training Services",
    "20550010": "Tobacco",
    "20550020": "Food Distribution",
    "20550030": "Grocery Stores",
    "20560010": "Tobacco Products",
    "20610010": "Biotechnology",
    "20620010": "Drug Manufacturers — General",
    "20620020": "Drug Manufacturers — Specialty & Generic",
    "20630010": "Healthcare Plans",
    "20645010": "Drug Manufacturers — Specialty",
    "20645020": "Pharmaceutical Retailers",
    "20645030": "Health Information Services",
    "20650010": "Medical Devices",
    "20650020": "Medical Instruments & Supplies",
    "20660010": "Medical Diagnostics & Research",
    "20670010": "Medical Distribution",
    "20710010": "Utilities — Independent Power",
    "20710020": "Utilities — Renewable",
    "20720010": "Utilities — Regulated Water",
    "20720020": "Utilities — Regulated Electric",
    "20720030": "Utilities — Regulated Gas",
    "20720040": "Utilities — Diversified",
    "30810010": "Telecom Services",
    "30820010": "Advertising Agencies",
    "30820020": "Publishing",
    "30820030": "Broadcasting",
    "30820040": "Entertainment",
    "30830010": "Internet Content & Information",
    "30830020": "Online Entertainment",
    "30910010": "Oil & Gas Drilling",
    "30910020": "Oil & Gas E&P",
    "30910030": "Oil & Gas Integrated",
    "30910040": "Oil & Gas Midstream",
    "30910050": "Oil & Gas Refining & Marketing",
    "30910060": "Oil & Gas Equipment & Services",
    "30920010": "Thermal Coal",
    "30920020": "Uranium",
    "31010010": "Aerospace & Defense",
    "31020010": "Specialty Business Services",
    "31020020": "Consulting Services",
    "31020030": "Rental & Leasing Services",
    "31020040": "Security & Protection Services",
    "31020050": "Staffing & Employment Services",
    "31030010": "Conglomerates",
    "31040010": "Engineering & Construction",
    "31040020": "Infrastructure Operations",
    "31040030": "Building Products & Equipment",
    "31050010": "Farm & Heavy Construction Machinery",
    "31060010": "Industrial Distribution",
    "31070010": "Business Equipment & Supplies",
    "31070020": "Specialty Industrial Machinery",
    "31070030": "Metal Fabrication",
    "31070040": "Pollution & Treatment Controls",
    "31070050": "Trucking",
    "31070060": "Electrical Equipment & Parts",
    "31080010": "Airports & Air Services",
    "31080020": "Airlines",
    "31080030": "Railroads",
    "31080040": "Marine Shipping",
    "31080050": "Trucking",
    "31080060": "Integrated Freight & Logistics",
    "31090010": "Waste Management",
    "31110010": "Information Technology Services",
    "31110020": "Software — Application",
    "31110030": "Software — Infrastructure",
    "31120010": "Communication Equipment",
    "31120020": "Computer Hardware",
    "31120030": "Consumer Electronics",
    "31120040": "Electronic Components",
    "31120050": "Electronics & Computer Distribution",
    "31120060": "Scientific & Technical Instruments",
    "31130010": "Semiconductor Equipment & Materials",
    "31130020": "Semiconductors",
    "31130030": "Solar",
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

_mstar_ext: dict = {}
_sub_ext:   dict = {}

# ── Model loading ─────────────────────────────────────────────────────────────
T1_READY = T2_READY = False
T1_ASSETS = T2_EXTRA = None

print(f"Models dir: {MODELS_DIR} — exists: {MODELS_DIR.exists()}")

try:
    T1_ASSETS = {
        "vectorizer": joblib.load(MODELS_DIR / "cascade_vectorizer.pkl"),
        "l1":         joblib.load(MODELS_DIR / "cascade_L1_svm.joblib"),
        "l2":         joblib.load(MODELS_DIR / "cascade_L2_models.joblib"),
        "l3":         joblib.load(MODELS_DIR / "cascade_L3_models.joblib"),
    }
    T1_READY = True
    print("Task 1 cascade: OK")
except Exception as e:
    print(f"Task 1 FAILED: {e}")

try:
    T2_EXTRA = {
        "seg_vec": joblib.load(MODELS_DIR / "t2_cascade_seg_vec.pkl"),
        "l4":      joblib.load(MODELS_DIR / "t2_cascade_L4_seg.joblib"),
    }
    T2_READY = T1_READY
    print("Task 2 L4: OK")
except Exception as e:
    print(f"Task 2 FAILED: {e}")

for path, store in [
    (MODELS_DIR / "mstar_labels_full.json", _mstar_ext),
    (MODELS_DIR / "sub_industry_labels.json", _sub_ext),
]:
    try:
        store.update(json.loads(path.read_text(encoding="utf-8")))
    except Exception:
        pass


def _get_mstar_label(code: str) -> str:
    return MSTAR_LABELS.get(code) or _mstar_ext.get(code) or f"Industry {code}"

def _get_sub_label(code: str) -> str:
    return SUBINDUSTRY_LABELS.get(code) or _sub_ext.get(code) or f"Sub-industry {code}"


# ── Core inference (returns dict — used by both UI and REST API) ──────────────
def _softmax(scores: np.ndarray) -> np.ndarray:
    s = np.asarray(scores, dtype=np.float64); s -= s.max()
    e = np.exp(s); return e / e.sum()

def _rank(artifact: dict, X_row, top_n: int = 3):
    if artifact["type"] == "constant":
        label = str(artifact["value"])
        return label, 100.0, [{"rank": 1, "label": label, "confidence": 100.0}]
    clf    = artifact["model"]
    scores = clf.decision_function(X_row)
    margins = np.array([-scores[0], scores[0]]) if np.ndim(scores) == 1 else np.asarray(scores[0])
    probs  = _softmax(margins)
    order  = np.argsort(probs)[::-1][:top_n]
    alts   = [{"rank": int(r)+1, "label": str(clf.classes_[i]),
               "confidence": round(float(probs[i])*100, 1)} for r, i in enumerate(order)]
    return str(clf.classes_[int(order[0])]), round(float(probs[int(order[0])])*100, 1), alts


def _predict_core(text: str) -> dict:
    """Raw prediction — returns structured dict for both UI and API."""
    if not T1_READY:
        return {"error": "Models offline"}

    X = T1_ASSETS["vectorizer"].transform([text])
    sector, s_conf, _ = _rank(T1_ASSETS["l1"], X)
    l2 = T1_ASSETS["l2"].get(sector)
    if not l2: raise KeyError(f"No L2 for sector {sector}")
    group, g_conf, _  = _rank(l2, X)
    l3 = T1_ASSETS["l3"].get(group)
    if not l3: raise KeyError(f"No L3 for group {group}")
    mstar, m_conf, alts = _rank(l3, X)

    mstar_label = _get_mstar_label(mstar)
    t1_conf     = round(min(s_conf, g_conf, m_conf), 1)

    task2 = None
    if T2_READY:
        try:
            X_seg = T2_EXTRA["seg_vec"].transform([text])
            l4    = T2_EXTRA["l4"].get(mstar)
            if l4:
                sub, sub_conf, sub_alts = _rank(l4, X_seg)
                task2 = {
                    "code":              sub,
                    "subindustry_name":  _get_sub_label(sub),
                    "confidence_percent": sub_conf,
                    "alternatives": [
                        {"code": a["label"], "subindustry_name": _get_sub_label(a["label"]),
                         "confidence_percent": a["confidence"]}
                        for a in sub_alts
                    ],
                }
        except Exception:
            pass

    return {
        "mstar_code":    mstar,
        "mstar_label":   mstar_label,
        "confidence_t1": t1_conf,
        "sector_code":   sector,
        "group_code":    group,
        "alternatives_t1": [
            {"rank": a["rank"], "code": a["label"],
             "label": _get_mstar_label(a["label"]), "confidence": a["confidence"]}
            for a in alts
        ],
        "cascade_path": f"Sector {sector} ({s_conf:.0f}%) → Group {group} ({g_conf:.0f}%) → {mstar} ({m_conf:.0f}%)",
        "task2": task2,
        "sub_code":  task2["code"]             if task2 else None,
        "sub_label": task2["subindustry_name"] if task2 else None,
        "confidence_t2": task2["confidence_percent"] if task2 else None,
        "alternatives_t2": [
            {"rank": i+1, "code": a["code"], "label": a["subindustry_name"],
             "confidence": a["confidence_percent"]}
            for i, a in enumerate(task2.get("alternatives", []))
        ] if task2 else [],
    }


# ── Gradio UI predict function ────────────────────────────────────────────────
def predict(text: str):
    text = text.strip()
    if not text:
        return "Please enter a company description.", "", "", ""
    if not T1_READY:
        return "Models offline — check Space logs.", "", "", ""
    try:
        d = _predict_core(text)
        if "error" in d:
            return d["error"], "", "", ""

        t1_md = (
            f"### {d['mstar_label']}\n"
            f"**Code:** `{d['mstar_code']}` &nbsp;|&nbsp; **Confidence:** {d['confidence_t1']}%\n\n"
            f"*{d['cascade_path']}*"
        )
        t2_md = ""
        if d["task2"]:
            t2_md = (
                f"### {d['sub_label']}\n"
                f"**Code:** `{d['sub_code']}` &nbsp;|&nbsp; **Confidence:** {d['confidence_t2']:.1f}%\n\n"
                f"*Constrained by Task 1 → {d['mstar_label']}*"
            )
        else:
            t2_md = f"Sub-industry N/A for `{d['mstar_code']}`"

        alt_lines = "\n".join(
            f"{a['rank']}. {a['label']} (`{a['code']}`) — {a['confidence']}%"
            for a in d["alternatives_t1"]
        )
        return t1_md, t2_md, d["cascade_path"], alt_lines

    except Exception as e:
        return f"Error: {e}", "", "", ""


# ── Gradio UI ─────────────────────────────────────────────────────────────────
EXAMPLES = [
    ["Apple Inc. designs and sells consumer electronics, software, and online services. Products include iPhone, Mac, iPad, Apple Watch, and services like the App Store and iCloud."],
    ["JPMorgan Chase operates as a global financial services firm providing investment banking, commercial banking, financial transaction processing, asset management and private banking."],
    ["NVIDIA designs graphics processing units for gaming, data center AI, and autonomous vehicles. Revenue is driven by data center GPU sales and automotive platform partnerships."],
    ["ExxonMobil explores, produces, and refines petroleum products. Operates in upstream, downstream, and chemical segments across global markets."],
    ["Pfizer discovers, develops, and commercializes biopharmaceutical products including vaccines, oncology therapies, and rare disease treatments."],
    ["The company operates a network of community banks providing commercial lending, retail deposits, residential mortgage origination, and small business banking services."],
]

STATUS  = "✅ Models loaded" if T1_READY else "❌ Models NOT loaded"
T1_BADGE = "145 classes · cascade SVM" if T1_READY else "offline"
T2_BADGE = "428 classes · 55.44% F1"  if T2_READY else "offline"

with gr.Blocks(
    title="TAVSS — GECS Industry Classifier",
    theme=gr.themes.Soft(),
) as demo:
    gr.Markdown(f"""
# TAVSS — GECS Industry Classifier
**MGT 599 Capstone · Group 4 · DePaul University**

<span style="background:#1e293b;color:#38bdf8;padding:2px 10px;border-radius:4px;font-size:12px;font-family:monospace">Task 1 — {T1_BADGE}</span> &nbsp;
<span style="background:#1e293b;color:#38bdf8;padding:2px 10px;border-radius:4px;font-size:12px;font-family:monospace">Task 2 — {T2_BADGE}</span>

*{STATUS}*
""")
    with gr.Row():
        with gr.Column(scale=1):
            text_input = gr.Textbox(label="Company Description",
                placeholder="Paste a company's business description…", lines=7)
            submit_btn = gr.Button("Classify →", variant="primary", size="lg")
            gr.Examples(examples=EXAMPLES, inputs=[text_input], label="Examples")
        with gr.Column(scale=1):
            gr.Markdown("**Task 1 — GECS Industry**")
            t1_out = gr.Markdown()
            gr.Markdown("---")
            gr.Markdown("**Task 2 — Sub-Industry**")
            t2_out = gr.Markdown()
    with gr.Accordion("Cascade details", open=False):
        cascade_out = gr.Textbox(label="Full cascade path", interactive=False)
        alts_out    = gr.Textbox(label="Top-3 alternatives", interactive=False, lines=4)

    submit_btn.click(fn=predict, inputs=[text_input],
                     outputs=[t1_out, t2_out, cascade_out, alts_out])
    text_input.submit(fn=predict, inputs=[text_input],
                      outputs=[t1_out, t2_out, cascade_out, alts_out])

    gr.Markdown("*Built with [breezeml](https://pypi.org/project/breezeml/) — `pip install breezeml`*")


# ── FastAPI app — Gradio + REST endpoints on one port ─────────────────────────
app = FastAPI()

@app.get("/health")
def health():
    return {
        "ok": T1_READY,
        "t1_ready": T1_READY,
        "t2_ready": T2_READY,
        "model": "cascade-svm-145-class",
    }

async def _json_predict(request: Request):
    try:
        payload  = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)

    text = str(payload.get("text") or payload.get("company_text") or "").strip()
    if not text:
        return JSONResponse({"error": "text or company_text is required"}, status_code=400)

    try:
        d = _predict_core(text)
        if "error" in d:
            return JSONResponse({"error": d["error"]}, status_code=503)

        # Return in format the Vercel frontend expects
        return JSONResponse({
            "success":       True,
            "engine":        "cascade-svm",
            "model_version": "tavss-cascade-v1",
            # flat fields (LiveDemo.tsx normalizePredictResponse reads these)
            "mstar_code":    d["mstar_code"],
            "mstar_label":   d["mstar_label"],
            "confidence_t1": d["confidence_t1"],
            "alternatives_t1": d["alternatives_t1"],
            "sub_code":      d["sub_code"],
            "sub_label":     d["sub_label"],
            "confidence_t2": d["confidence_t2"],
            "alternatives_t2": d["alternatives_t2"],
            # nested fields (also handled by normalizePredictResponse)
            "task1": {
                "code":         d["mstar_code"],
                "industry_name": d["mstar_label"],
                "confidence_percent": d["confidence_t1"],
            },
            "task2": d["task2"],
            "route_reason": d["cascade_path"],
        })
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)

# Both aliases hit the same handler
app.add_api_route("/api/predict",           _json_predict, methods=["POST"])
app.add_api_route("/api/predict_legendary", _json_predict, methods=["POST"])
app.add_api_route("/predict",               _json_predict, methods=["POST"])

# Mount Gradio UI at root
app = gr.mount_gradio_app(app, demo, path="/")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
