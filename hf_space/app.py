"""
GECS Cascade SVM Classifier — Hugging Face Space
Task 1: Sector->Group->MSTAR  (88.90% Macro F1, 145 classes)
Task 2: Hybrid cascade T1->MSTAR + L4 sub-industry (55.41% Macro F1, 428 classes)
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import gradio as gr

MODELS_DIR = Path(__file__).resolve().parent / "models"

# ── Label maps ────────────────────────────────────────────────────────────────
MSTAR_LABELS = {
    "10110010": "Oil & Gas Integrated",         "10110020": "Oil & Gas E&P",
    "10110030": "Oil & Gas Midstream",           "10120010": "Coal & Consumable Fuels",
    "10130010": "Agricultural Inputs",           "10140010": "Aluminum",
    "10140020": "Copper",                        "10200010": "Chemicals — Specialty",
    "10200020": "Chemicals — Commodity",         "10200030": "Diversified Chemicals",
    "10310010": "Diversified Financial Services","10320010": "Capital Markets",
    "10320020": "Regional Banks",               "10320030": "Diversified Banks",
    "10320040": "Insurance — Life & Health",    "10320050": "Insurance — P&C",
    "10340010": "Asset Management",             "10340060": "Insurance — Multi-line",
    "20524010": "Healthcare Plans",             "20525010": "Medical Care Facilities",
    "20527010": "Drug Manufacturers — General", "20527020": "Biotechnology",
    "20527050": "Drug Manufacturers — Specialty","20528010": "Medical Devices",
    "20528020": "Medical Instruments & Supplies","20529010": "Consumer Electronics",
    "20650010": "Medical Equipment & Instruments","21012010": "Apparel Manufacturing",
    "21012020": "Footwear & Accessories",       "21021010": "Discount Stores",
    "21022020": "Specialty Retail",             "21022030": "Department Stores",
    "30610010": "REIT — Retail",               "30610020": "REIT — Office",
    "30610030": "REIT — Industrial",           "30610040": "REIT — Healthcare",
    "30620010": "Real Estate Services",        "30810010": "Electronic Components",
    "30810020": "Electronic Manufacturing Services","30810030": "Telecom Services",
    "30820010": "Internet Content & Information","30820020": "Software — Application",
    "30820030": "Software — Infrastructure",   "30830010": "Internet Search & AI Services",
    "30830020": "Entertainment",               "30830030": "Broadcasting & Media",
    "30910020": "Oil & Gas Equipment & Services","31020010": "Aerospace & Defense",
    "31020020": "Industrial Machinery",        "31020030": "Diversified Industrials",
    "31110030": "IT Services & Cloud Computing","31120020": "Electrical Equipment & Parts",
    "31120060": "Scientific & Technical Instruments","31130010": "Semiconductors",
    "31130020": "Semiconductor Equipment",
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


def _get_mstar_label(code: str) -> str:
    if code in MSTAR_LABELS:
        return MSTAR_LABELS[code]
    if code in _mstar_ext:
        return _mstar_ext[code]
    return f"Industry {code}"


def _get_sub_label(code: str) -> str:
    if code in SUBINDUSTRY_LABELS:
        return SUBINDUSTRY_LABELS[code]
    if code in _sub_ext:
        return _sub_ext[code]
    return f"Sub-industry {code}"


# ── Inlined cascade prediction ────────────────────────────────────────────────

def _softmax(scores: np.ndarray) -> np.ndarray:
    s = np.asarray(scores, dtype=np.float64)
    s = s - s.max()
    e = np.exp(s)
    return e / e.sum()


def _rank_artifact(artifact: dict, X_row, top_n: int = 3):
    if artifact["type"] == "constant":
        label = str(artifact["value"])
        return label, 100.0, [{"rank": 1, "label": label, "confidence": 100.0}]
    clf = artifact["model"]
    scores = clf.decision_function(X_row)
    if np.ndim(scores) == 1:
        margins = np.array([-scores[0], scores[0]], dtype=np.float64)
    else:
        margins = np.asarray(scores[0], dtype=np.float64)
    probs = _softmax(margins)
    order = np.argsort(probs)[::-1][:top_n]
    alts = [{"rank": int(r) + 1, "label": str(clf.classes_[i]),
              "confidence": round(float(probs[i]) * 100.0, 1)}
            for r, i in enumerate(order)]
    best = int(order[0])
    return str(clf.classes_[best]), round(float(probs[best]) * 100.0, 1), alts


# ── Model loading ─────────────────────────────────────────────────────────────
T1_READY = T2_READY = False
T1_ASSETS = T2_ASSETS = None
_sub_ext = {}
_mstar_ext = {}

print(f"Models directory: {MODELS_DIR}")
print(f"Models exist: {MODELS_DIR.exists()}")

try:
    T1_ASSETS = {
        "vectorizer": joblib.load(MODELS_DIR / "cascade_vectorizer.pkl"),
        "l1":         joblib.load(MODELS_DIR / "cascade_L1_svm.joblib"),
        "l2":         joblib.load(MODELS_DIR / "cascade_L2_models.joblib"),
        "l3":         joblib.load(MODELS_DIR / "cascade_L3_models.joblib"),
    }
    T1_READY = True
    print("Task 1 cascade loaded.")
except Exception as e:
    print(f"Task 1 load failed: {e}")

try:
    T2_EXTRA = {
        "seg_vec": joblib.load(MODELS_DIR / "t2_cascade_seg_vec.pkl"),
        "l4":      joblib.load(MODELS_DIR / "t2_cascade_L4_seg.joblib"),
    }
    T2_READY = T1_READY
    print("Task 2 L4 loaded.")
except Exception as e:
    print(f"Task 2 load failed: {e}")

for path, store in [
    (MODELS_DIR / "sub_industry_labels.json", _sub_ext),
    (MODELS_DIR / "mstar_labels_full.json",   _mstar_ext),
]:
    try:
        store.update(json.loads(path.read_text(encoding="utf-8")))
    except Exception:
        pass


# ── Inference ─────────────────────────────────────────────────────────────────

def predict(text: str):
    text = text.strip()
    if not text:
        return "Please enter a company description.", "", "", ""

    if not T1_READY:
        return (
            "Models offline — see Space logs for setup instructions.",
            "",
            "Models not loaded. Please check that model files are present in the 'models/' directory.",
            "",
        )

    try:
        X = T1_ASSETS["vectorizer"].transform([text])
        sector, s_conf, _ = _rank_artifact(T1_ASSETS["l1"], X)
        l2 = T1_ASSETS["l2"].get(sector)
        if l2 is None:
            raise KeyError(f"No L2 for sector {sector}")
        group, g_conf, _ = _rank_artifact(l2, X)
        l3 = T1_ASSETS["l3"].get(group)
        if l3 is None:
            raise KeyError(f"No L3 for group {group}")
        mstar, m_conf, mstar_alts = _rank_artifact(l3, X)

        mstar_label   = _get_mstar_label(mstar)
        t1_confidence = round(min(s_conf, g_conf, m_conf), 1)
        cascade_t1    = (
            f"Sector {sector} ({s_conf:.0f}%) -> "
            f"Group {group} ({g_conf:.0f}%) -> "
            f"MSTAR {mstar} ({m_conf:.0f}%)"
        )

        if T2_READY:
            try:
                X_seg = T2_EXTRA["seg_vec"].transform([text])
                l4 = T2_EXTRA["l4"].get(mstar)
                if l4 is None:
                    raise KeyError(f"No L4 for MSTAR {mstar}")
                sub, sub_conf, sub_alts = _rank_artifact(l4, X_seg)
                sub_label   = _get_sub_label(sub)
                t2_result   = (
                    f"**Sub-industry:** {sub_label}  \n"
                    f"**Code:** `{sub}`  \n"
                    f"**Confidence:** {sub_conf:.1f}%  \n"
                    f"**Cascade:** {cascade_t1} -> Sub {sub} ({sub_conf:.0f}%)"
                )
            except KeyError:
                sub_label = f"{mstar_label} (sub N/A)"
                t2_result = f"Sub-industry N/A (MSTAR `{mstar}` not in T2 training set)"
        else:
            t2_result = "Task 2 model offline."

        t1_result = (
            f"**Industry:** {mstar_label}  \n"
            f"**Code:** `{mstar}`  \n"
            f"**Confidence:** {t1_confidence}%"
        )
        alt_list = "\n".join(
            f"{a['rank']}. {_get_mstar_label(a['label'])} (`{a['label']}`) — {a['confidence']}%"
            for a in mstar_alts
        )

        return t1_result, t2_result, cascade_t1, alt_list

    except Exception as e:
        return f"Error: {e}", "", "", ""


# ── Gradio UI ─────────────────────────────────────────────────────────────────

EXAMPLES = [
    ["Apple Inc. designs and sells consumer electronics, software, and online services. Products include iPhone, Mac, iPad, Apple Watch, and services like the App Store and iCloud."],
    ["JPMorgan Chase & Co. operates as a global financial services firm and banking institution. It provides investment banking, financial services, and asset management."],
    ["NVIDIA Corporation designs graphics processing units and system-on-chip units. It develops software and hardware for gaming, professional visualization, data centers, and autonomous vehicles."],
    ["ExxonMobil Corporation explores, produces, and refines petroleum and petrochemical products. It operates in the upstream, downstream, and chemical segments."],
    ["Pfizer Inc. discovers, develops, manufactures, and markets healthcare products including pharmaceuticals, vaccines, and consumer healthcare products."],
]

STATUS = "Models loaded" if T1_READY else "Models NOT loaded — add model files to models/ directory"
T1_BADGE = "88.90% Macro F1 · 145 classes" if T1_READY else "offline"
T2_BADGE = "55.41% Macro F1 · 428 classes" if T2_READY else "offline"

with gr.Blocks(
    title="GECS Industry Classifier",
    theme=gr.themes.Soft(),
    css="""
    .badge { background: #1e293b; color: #38bdf8; padding: 2px 8px;
             border-radius: 4px; font-size: 12px; font-family: monospace; }
    .result-box { background: #f8fafc; border: 1px solid #e2e8f0;
                  border-radius: 8px; padding: 16px; }
    """
) as demo:
    gr.Markdown(f"""
# GECS Industry Classifier
**MGT 599 Capstone · Group 4 · Hybrid Cascade SVM**

<span class="badge">Task 1 — {T1_BADGE}</span> &nbsp;
<span class="badge">Task 2 — {T2_BADGE}</span>

*Status: {STATUS}*
""")

    with gr.Row():
        with gr.Column(scale=1):
            text_input = gr.Textbox(
                label="Company Description",
                placeholder="Enter a company's business description, segment info, or LongProfile...",
                lines=6,
            )
            submit_btn = gr.Button("Classify", variant="primary", size="lg")
            gr.Examples(examples=EXAMPLES, inputs=[text_input], label="Examples")

        with gr.Column(scale=1):
            t1_out = gr.Markdown(label="Task 1 — Industry (MSTAR)")
            t2_out = gr.Markdown(label="Task 2 — Sub-Industry")

    with gr.Accordion("Details", open=False):
        cascade_out = gr.Textbox(label="Cascade Path (T1)", interactive=False)
        alts_out    = gr.Textbox(label="Top-3 MSTAR Alternatives", interactive=False, lines=4)

    submit_btn.click(
        fn=predict,
        inputs=[text_input],
        outputs=[t1_out, t2_out, cascade_out, alts_out],
    )
    text_input.submit(
        fn=predict,
        inputs=[text_input],
        outputs=[t1_out, t2_out, cascade_out, alts_out],
    )

    gr.Markdown("""
---
**Architecture:** 4-level cascade — TF-IDF + LinearSVC at each level
**Task 1:** Sector (L1) -> Group (L2) -> MSTAR code (L3) — +29pp over DeBERTa baseline
**Task 2:** T1 cascade routes to MSTAR, then L4 SVM picks sub-industry — +19pp over DeBERTa

To add model files: copy `models/*.joblib`, `models/*.pkl`, and `models/*.json`
from the GitHub repo into the `models/` directory of this Space.
""")

demo.launch(server_name="0.0.0.0", server_port=7860)
