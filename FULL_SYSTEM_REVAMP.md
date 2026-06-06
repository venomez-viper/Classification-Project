# GECS-Sage — Full System Revamp Specification

**Companion to:** `HANDOFF_PLAYBOOK.md`
**Purpose:** Complete instructions for the frontend, backend, deployment, and demo system that ships with the submission.
**Owner:** Codex executes most of this. Akash builds the ML core (covered in `HANDOFF_PLAYBOOK.md`).
**Deadline:** Live, deployed, demoed by Monday May 18, 2026.

This document is the **complete spec**. Hand it to Codex (or any coding LLM) along with `HANDOFF_PLAYBOOK.md` and they should be able to build the entire system without further conversation.

---

## 0. Naming and brand identity

Use this consistently across every UI surface, doc, and slide.

| Field | Value |
|---|---|
| Product name | **GECS-Sage** |
| Tagline | *"Industry classification grounded in Morningstar's own taxonomy."* |
| Version | v1.0 |
| Audience | Morningstar Reference Entity Data (RED) team |
| Primary color | Navy `#1F3A5F` |
| Secondary color | Teal `#0E6B6E` |
| Accent (positive) | Sage `#7A9E7E` |
| Accent (warning) | Gold `#D4A93F` |
| Accent (negative / defer) | Coral `#E07856` |
| Body text | Dark gray `#3D4951` |
| Background light | `#F7F7F7` |
| Background dark | `#0F1418` |
| Headings font | Inter / SF Pro / system-ui |
| Mono font | JetBrains Mono / Consolas |
| Brand voice | Precise, honest, enterprise-mature. No emojis in production UI. No marketing fluff. |

**Style references:** Linear, Vercel, Stripe Dashboard. **Avoid:** generic SaaS gradient hero, glassmorphism, AI-stock-photo banners.

---

## 1. System map — what gets built and where it lives

```
GECS-Sage Repo
├── serve/                              [Codex builds. Local Flask, patched.]
│   ├── app.py                          patched server_legendary.py
│   ├── llm_judge.py                    Ollama Qwen2.5-3B wrapper
│   ├── predictions.sqlite              auto-created log
│   └── requirements.txt
│
├── frontend/                           [Codex builds. Next.js 13 app router.]
│   ├── app/
│   │   ├── layout.tsx                  navy top nav, brand bar, footer
│   │   ├── page.tsx                    home / classifier
│   │   ├── history/page.tsx            prediction history table
│   │   ├── metrics/page.tsx            latency + confidence dashboards
│   │   └── methodology/page.tsx        the audit story page
│   ├── components/
│   │   ├── PredictionCard.tsx          top-3, reasoning, GECS quote, override
│   │   ├── ConfidenceBar.tsx           calibrated probability bar
│   │   ├── ReasoningTrace.tsx          step-by-step LLM judge output
│   │   ├── TaxonomyDefinition.tsx      official GECS quote panel
│   │   ├── ProcessingTrace.tsx         per-stage latency display
│   │   ├── AlternativesList.tsx        2nd and 3rd choices with rejection reasons
│   │   ├── Hierarchy.tsx               sector → group → industry breadcrumb
│   │   └── OverrideDialog.tsx          dropdown of 145 codes for analyst override
│   └── lib/api.ts                      typed client for /predict, /history, /metrics
│
├── hf_space/                           [Codex builds. The deployed app.]
│   ├── app.py                          Gradio entry point
│   ├── model_assets/                   ONNX or PyTorch model + vectorizers
│   │                                   (No FAISS — use np.dot for top-K nearest neighbors.
│   │                                    42k rows × 768d at FP32 is ~130MB; matmul on CPU
│   │                                    takes ~10ms. FAISS is unnecessary overhead.)
│   ├── data_assets/
│   │   ├── train_embeddings.npy        precomputed BGE embeddings for RAC
│   │   └── train_labels.npy            corresponding training labels
│   ├── gecs_taxonomy.json              copy of the 145 GECS definitions
│   ├── requirements.txt
│   └── README.md                       the HF Space card
│
├── docs/
│   ├── DEPLOYMENT_RUNBOOK.md           [Codex writes]
│   ├── architecture/system_diagram.png [Codex writes]
│   ├── presentation/GECS_Sage_Final.pptx [Codex writes]
│   └── [existing docs unchanged]
│
└── README.md                           [Codex revamps]
```

---

## 2. The user journey — what Morningstar will actually see

Walk through this end-to-end. Every screen below has to ship.

### Screen A — The landing / classifier screen (`frontend/app/page.tsx`)

```
┌────────────────────────────────────────────────────────────────────────────────┐
│  GECS-Sage v1.0    ·    Classifier  |  History  |  Metrics  |  Methodology     │
├────────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│  GECS Industry & Business Activity Classification                              │
│  Grounded in Morningstar's 2019 GECS taxonomy.                                 │
│                                                                                │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │ Paste a company segment description...                                   │  │
│  │                                                                          │  │
│  │                                                                          │  │
│  └──────────────────────────────────────────────────────────────────────────┘  │
│                                                                                │
│  [ Classify ]   Examples: [Regional Bank] [Pharma Generic] [Conglomerate]      │
│                                                                                │
└────────────────────────────────────────────────────────────────────────────────┘
```

Layout: navy top nav (fixed). Brand on left, four nav tabs on right. Below, single-column content max-width 880px center-aligned. Tailwind. No marketing copy, no hero image, no gradient.

The three example chips load pre-built test cases that show the system handling easy / hard / ambiguous cases. **This is critical** — when the Morningstar rep clicks "Conglomerate," they see the system DEFER, not pretend.

### Screen B — The prediction result (rendered below the input, same page)

```
┌────────────────────────────────────────────────────────────────────────────────┐
│  PRIMARY PREDICTION                                                            │
│                                                                                │
│  Task 1 (Industry)                                                             │
│  10320020   Banks — Regional                                          84% ████ │
│                                                                                │
│  Task 2 (Business Activity)                                                    │
│  10320020-02   Commercial Lending                                     78% ███▌ │
│                                                                                │
│  Confidence: Calibrated via CalibratedClassifierCV (sigmoid).                  │
│  Threshold for analyst review: <70%.                                           │
├────────────────────────────────────────────────────────────────────────────────┤
│  OFFICIAL GECS DEFINITION  (Morningstar 2019 reference, p. 13)                │
│                                                                                │
│  "Regional, diverse financial institutions serving the corporate,              │
│   government, and consumer needs of retail banking, investment banking,        │
│   trust management, credit cards, mortgage banking..."                         │
│                                                                                │
│  Matched on phrase: "regional retail banking"                                  │
├────────────────────────────────────────────────────────────────────────────────┤
│  ALTERNATIVES CONSIDERED                                                       │
│                                                                                │
│  ○ 10320010   Banks — Diversified                                       9%     │
│    Rejected: segment specifies regional focus, not global operations.          │
│                                                                                │
│  ○ 10360010   Credit Services                                           3%     │
│    Rejected: broader credit-services scope not matched in segment text.        │
├────────────────────────────────────────────────────────────────────────────────┤
│  REASONING TRACE  (Qwen2.5-3B via local Ollama)             [Hide / Show]      │
│                                                                                │
│  Step 1. The segment text mentions "regional retail banks" and                 │
│          "commercial lending" — primary economic activity is banking.          │
│  Step 2. Sector: 103 Financial Services.                                       │
│  Step 3. Within sector 103, group 10320 Banks contains three sub-codes:        │
│          Banks-Diversified (10320010), Banks-Regional (10320020),              │
│          Mortgage Finance (10320030).                                          │
│  Step 4. The segment specifies regional + commercial → Banks-Regional.         │
│  Step 5. FINAL_CODE: 10320020                                                  │
├────────────────────────────────────────────────────────────────────────────────┤
│  PROCESSING TRACE                                          [Hide / Show]       │
│                                                                                │
│  TF-IDF + multi-encoder retrieval (BreezeML)               22 ms               │
│  RAG over 145 GECS official definitions                     18 ms              │
│  ModernBERT-base classifier (ONNX INT8)                     80 ms              │
│  Calibrated probability head                                 5 ms              │
│  Hierarchical Task 2 constraint                              3 ms              │
│  Qwen2.5-3B reasoning trace (via Ollama)                  fired                │
│                                                                                │
│  Total latency: 128 ms                                                         │
├────────────────────────────────────────────────────────────────────────────────┤
│                                                                                │
│  [ Accept prediction ]   [ Override... ]   [ Flag for review ]                 │
│                                                                                │
└────────────────────────────────────────────────────────────────────────────────┘
```

Every block above must render. Every number must be real (no placeholder text in production). If reasoning trace can't fire (Ollama not available on HF Space), the section says *"Reasoning trace available in local deploy"* and links to the GitHub README. Don't fake it.

### Screen C — Low-confidence deferral

When the classifier's top-1 confidence is below 0.70, the layout changes:

```
┌────────────────────────────────────────────────────────────────────────────────┐
│  ⚠  LOW CONFIDENCE — RECOMMEND ANALYST REVIEW                                  │
│                                                                                │
│  No candidate cleared the 0.70 calibrated-probability threshold.               │
│  Top three candidates shown below for analyst review.                          │
│                                                                                │
│  This often signals a multi-segment conglomerate or a segment description      │
│  that spans multiple GECS leaves. Recommended action: route to RED's senior    │
│  analyst review queue.                                                         │
├────────────────────────────────────────────────────────────────────────────────┤
│  Candidate 1   31030010  Diversified Industrials                  44%          │
│  Candidate 2   31020010  Industrial Machinery                     31%          │
│  Candidate 3   10310010  Asset Management                         18%          │
│                                                                                │
│  [ View all candidate definitions ]   [ Send to review queue ]                 │
└────────────────────────────────────────────────────────────────────────────────┘
```

**This screen is the most important one to show Morningstar.** It is what separates a hireable product from a science demo.

### Screen D — History (`frontend/app/history/page.tsx`)

Plain sortable table. Columns:
- Timestamp
- Input excerpt (first 80 chars)
- Predicted Task 1 code + name
- Predicted Task 2 code + name
- Calibrated confidence
- Status (`accepted` / `overridden` / `flagged`)
- Latency (ms)

Pagination: 50 rows per page. Filter by status. No charts here — keep it dense and Morningstar-internal-tool-feeling.

### Screen E — Metrics dashboard (`frontend/app/metrics/page.tsx`)

Three KPI tiles + three small charts. Pulls from `GET /metrics`.

```
┌────────────────────────────────────────────────────────────────────────────────┐
│  Total predictions: 47          Median confidence: 0.78                        │
│  p50 latency: 95 ms             p95 latency: 182 ms                            │
│  Deferral rate (< 0.70): 18%    Override rate: 4%                              │
├────────────────────────────────────────────────────────────────────────────────┤
│  [Latency histogram bar chart — p50/p95/p99]                                   │
│  [Confidence histogram (10 buckets, 0.0–1.0)]                                  │
│  [Top predicted industries (last 24h)]                                         │
└────────────────────────────────────────────────────────────────────────────────┘
```

Use `recharts` (already in Next.js ecosystem). No fancy animations. Two-color charts (navy + teal). Honest data only — no fake high numbers.

### Screen F — Methodology page (`frontend/app/methodology/page.tsx`)

**This is your story page.** It tells the audit narrative in the UI itself, so anyone visiting the live URL sees what makes the project different.

Sections:
1. **The leakage we caught.** Big navy header. 88.90% → 60% chart embedded.
2. **How the system works.** Architecture diagram from `docs/architecture/system_diagram.png`.
3. **Grounded in your taxonomy.** Explains GECS PDF parsing, shows two example anchors.
4. **What we cannot solve.** Honest call-out about `31030010` Diversified Industrials.
5. **For Morningstar's RED team.** Workflow integration recommendation.

This page makes the legendary playbook a *visible artifact*, not just a talking point. **Build this. Morningstar will read it.**

---

## 3. Backend — patching `server_legendary.py`

### What stays
- Flask + Flask-CORS imports
- Existing `route_prediction` logic (the routing infrastructure is sound)
- Existing `taxonomy_crosswalk` loading
- The endpoint structure

### What gets replaced
- The softmax-on-decision-margin pseudo-confidence — **replace with `CalibratedClassifierCV.predict_proba()`**
- The DeBERTa placeholder — **replace with the ModernBERT artifact if available, else V10 (`models_v10/v10_calibrated.joblib`), else V13 (`models_v13/v13_linearsvc_c1.joblib` wrapped with `CalibratedClassifierCV` at startup)**. Log which artifact actually loaded.
- No `/health`, `/metrics`, `/history` endpoints — **add them**

### Required endpoints

| Method | Path | Returns |
|---|---|---|
| GET | `/health` | `{"status":"ok","model_version":"v1.0","backend":"modernbert","fallback":"v10","loaded_at":"..."}` |
| POST | `/predict` | The full prediction payload (see Section 4 below) |
| POST | `/feedback` | Records `{prediction_id, status: accepted|overridden|flagged, overridden_code?}` to SQLite |
| GET | `/history?limit=50&offset=0&status=...` | Last N predictions from SQLite |
| GET | `/metrics` | Aggregated metrics for the dashboard |
| GET | `/taxonomy/<code>` | Returns the official GECS definition for a single code (used by alternatives panel) |
| GET | `/docs` | (Optional) OpenAPI / Swagger UI — Flask doesn't have native, but `flasgger` or static HTML works |

### Codex prompt for the backend patch

> Patch the existing `server_legendary.py` Flask app. Do not rewrite — preserve `route_prediction`, `CASCADE_ASSETS`, `CROSSWALK`, `RouterThresholds`. Make these changes:
>
> 1. Replace the existing softmax-on-margin confidence calculation with `CalibratedClassifierCV.predict_proba()` outputs. Load the calibrated model from `models_v10/v10_calibrated.joblib` if it exists; otherwise fall back to `models_v13/v13_linearsvc_c1.joblib` (wrap it with `CalibratedClassifierCV(method='sigmoid', cv='prefit')` at startup to give it calibrated probabilities). Log which artifact loaded successfully.
> 2. Add a `/health` endpoint returning model version and load timestamp.
> 3. Add a `/feedback` POST endpoint that takes `{prediction_id, status, overridden_code}` and inserts into a SQLite database at `serve/predictions.sqlite`. Schema: `predictions(id TEXT PRIMARY KEY, ts INTEGER, input TEXT, task1_code TEXT, task1_conf REAL, task2_code TEXT, task2_conf REAL, status TEXT, overridden_code TEXT NULL, latency_ms INTEGER)`. Every `/predict` call also inserts a row with status='pending'.
> 4. Add a `/history` GET endpoint with optional `limit`, `offset`, and `status` query params.
> 5. Add a `/metrics` GET endpoint returning `{total_predictions, p50_latency_ms, p95_latency_ms, p99_latency_ms, confidence_histogram_10_buckets, top_predicted_industries_24h, deferral_rate, override_rate}`.
> 6. Add a `/taxonomy/<code>` endpoint returning the official GECS definition (read from `gecs_taxonomy.json`).
> 7. Modify the `/predict` response to include: top-3 alternatives with rejection reasons (computed from `predict_proba` ranking), the matched GECS-definition phrase (from anchor cosine similarity), the processing trace (per-stage latency in milliseconds), and the `prediction_id` (uuid4).
> 8. Add the optional `llm_judge` call when top-1 confidence is below 0.70 — wraps an Ollama call via the existing `llm_judge.py` module Codex Task 2 produces. If Ollama unreachable, fall back silently to top-1.
> 9. Preserve `route_prediction` — it stays.
>
> Do not introduce FastAPI. Keep Flask. Do not rewrite the whole file.

---

## 4. The canonical `/predict` response (lock this contract)

Every component on the frontend reads this. Lock the shape now.

```
POST /predict
Body: {"company_text": "...", "include_reasoning": true}

Response 200:
{
  "prediction_id": "uuid4",
  "task1": {
    "code": "10320020",
    "industry_name": "Banks — Regional",
    "sector_code": "103",
    "sector_name": "Financial Services",
    "group_code": "10320",
    "group_name": "Banks",
    "calibrated_confidence": 0.84,
    "official_definition": "...",
    "matched_phrase": "regional retail banking",
    "is_deferred": false
  },
  "task2": {
    "code": "10320020-02",
    "activity_name": "Commercial Lending",
    "calibrated_confidence": 0.78,
    "constrained_by_task1": true
  },
  "alternatives": [
    {
      "code": "10320010",
      "industry_name": "Banks — Diversified",
      "calibrated_confidence": 0.09,
      "rejection_reason": "segment specifies regional focus, not global operations"
    },
    {
      "code": "10360010",
      "industry_name": "Credit Services",
      "calibrated_confidence": 0.03,
      "rejection_reason": "broader credit-services scope not matched in segment text"
    }
  ],
  "reasoning": "Step 1. ... Step 5. FINAL_CODE: 10320020",
  "trace": {
    "tfidf_ms": 22,
    "anchor_retrieval_ms": 18,
    "encoder_ms": 80,
    "calibration_ms": 5,
    "task2_constraint_ms": 3,
    "llm_judge_ms": 0,
    "total_ms": 128
  },
  "model_version": "v1.0",
  "fallback_used": false
}
```

If anything is missing in the response, the frontend shows a placeholder *"not available"* — never silently hides it.

---

## 5. The Hugging Face Space (Gradio app)

The HF Space is the **public-facing demo**. It bundles everything into one deployable folder.

### File layout

```
hf_space/
├── app.py                        # Gradio entry point (Codex builds)
├── model_assets/
│   ├── modernbert_classifier.onnx   # quantized INT8 (Akash produces)
│   ├── meta_classifier.joblib       # calibrated ensemble (Akash produces)
│   ├── conglomerate_branch.joblib   # binary guard (Akash produces)
│   ├── per_class_thresholds.json
│   ├── tfidf_vec_seg.pkl
│   ├── tfidf_vec_long.pkl
│   └── scaler.pkl
├── data_assets/
│   ├── gecs_taxonomy.json
│   ├── train_embeddings.npy         # BGE-base train embeddings (~130MB)
│   ├── train_labels.npy             # parallel array of train labels
│   └── task1_to_task2_map.json
├── requirements.txt              # gradio, scikit-learn, onnxruntime, sentence-transformers
└── README.md                     # HF Space card with license, demo link, screenshots
```

### Gradio UI structure

Three tabs at the top of the Space:

1. **Classifier** — same prediction flow as the Next.js home page, but in Gradio components. Includes the three example chips.
2. **About / Methodology** — the audit story in markdown. Same content as `frontend/app/methodology/page.tsx`, just rendered via `gr.Markdown`.
3. **API** — shows the curl command for hitting the underlying prediction function programmatically.

Gradio's `gr.Examples` pre-populates the three sample inputs (regional bank, pharma generic, conglomerate). Latency target on HF free CPU: < 800ms (slightly looser than the local Flask 500ms target).

### Codex prompt for the HF Space

> Build `hf_space/app.py` as a Gradio app for GECS-Sage. Three tabs: Classifier, Methodology, API. The Classifier tab takes a text input, calls a `classify(text)` Python function that:
>
> 1. Loads `model_assets/modernbert_classifier.onnx` via `onnxruntime` (CPU only)
> 2. Loads `meta_classifier.joblib` (CalibratedClassifierCV)
> 3. Loads `gecs_taxonomy.json` for definition lookups
> 4. Loads `train_embeddings.npy` + `train_labels.npy` for nearest-neighbor retrieval (`np.dot` for top-K, no FAISS)
> 5. Returns a dict matching the `/predict` response schema in Section 4 of this spec
>
> Display the result as: a "Primary prediction" card with two colored bars for Task 1 and Task 2 confidence; an "Official GECS definition" markdown panel; an "Alternatives" expandable section with rejection reasons; a "Processing trace" expander showing per-stage latency.
>
> When Task 1 calibrated confidence is below 0.70, render a coral warning banner: *"Low confidence — recommend analyst review."* Show all three candidates and the suggested action.
>
> The Methodology tab is a `gr.Markdown` block rendering `methodology.md` (provided separately).
>
> The API tab shows a static code block with a `curl` example and the JSON schema.
>
> Style: dark mode default, navy/teal/coral palette matching the Next.js frontend. No emojis. Brand name "GECS-Sage" at the top.
>
> Include three `gr.Examples`: (1) regional bank description, (2) pharmaceutical generic, (3) conglomerate (designed to trigger the low-confidence path).

---

## 6. Model artifacts — what Akash hands to Codex on Tuesday night

After the Tuesday hard gate, the locked model needs to be packaged for deployment.

**Two acceptable bundle states — try the optimized one first, fall back if anything breaks.**

### Bundle A — Optimized (try first)

| Artifact | How produced | Size target |
|---|---|---|
| `modernbert_classifier.onnx` (INT8) | Export ModernBERT-base via `torch.onnx.export` then quantize via `optimum.onnxruntime.ORTQuantizer(approach='dynamic')` | ~150 MB |
| `meta_classifier.joblib` | The CalibratedClassifierCV ensemble | < 50 MB |
| `conglomerate_branch.joblib` | A small LogisticRegression on revenue features | < 1 MB |
| `tfidf_vec_seg.pkl`, `tfidf_vec_long.pkl` | The TF-IDF vectorizers | ~30 MB |
| `train_embeddings.npy` + `train_labels.npy` | BGE-base embeddings + labels for the simple nearest-neighbor RAC step (no FAISS) | ~130 MB + 1 MB |
| `gecs_taxonomy.json` | Already exists | < 200 KB |
| `task1_to_task2_map.json` | Verified during tonight's Task 2 build | < 50 KB |
| `per_class_thresholds.json` | Result of per-class threshold tuning | < 10 KB |

Total: ~350 MB. HF Space free tier allows 50 GB. Comfortable.

### Bundle B — Fallback (if ONNX export or INT8 quantization fails)

| Artifact | How produced | Size target |
|---|---|---|
| `modernbert_classifier.pt` (FP32 PyTorch) | Standard `torch.save(model.state_dict(), ...)` | ~600 MB |

Everything else identical. Bundle total ~800 MB. **Still fits HF Space free tier comfortably.** Inference latency goes from ~80ms to ~300ms on HF CPU — still under the 500ms p95 target.

### Hard rule

**Do not block the Wednesday deploy on getting ONNX quantization working.** If by Wednesday noon the INT8 path is still throwing errors, ship Bundle B with the FP32 PyTorch model. The audit story is what wins the room — not 80ms vs 300ms latency. Take the working bundle every time.

---

## 7. Deployment runbook (Codex writes `docs/DEPLOYMENT_RUNBOOK.md`)

The runbook must cover:

1. **Local dev (Flask backend + Next.js frontend)**
   - Prerequisites: Python 3.11, Node 20, optional Ollama
   - `pip install -r serve/requirements.txt`
   - `cd frontend && npm install`
   - `cd serve && python app.py` (port 5003)
   - `cd frontend && npm run dev` (port 3000)
   - Optional: `ollama serve` + `ollama pull qwen2.5:3b-instruct`

2. **Live HF Space deploy**
   - `cd hf_space && huggingface-cli login`
   - `huggingface-cli upload <user>/gecs-sage . --repo-type=space`
   - Visit `https://huggingface.co/spaces/<user>/gecs-sage`

3. **Docker (single-container option for Morningstar to self-host)**
   - Dockerfile in `serve/Dockerfile`
   - `docker build -t gecs-sage .`
   - `docker run -p 5003:5003 gecs-sage`
   - Image size target: < 1.5 GB

4. **Retraining pipeline**
   - When a new GECS code is added: update `gecs_taxonomy.json`, run `scripts/retrain_v10.py`, save new joblib, push to HF Space
   - Monthly cadence: full retrain on the latest task1_train + task2_train, ~30 min on CPU
   - Drift signal: weekly check of per-class F1 on a held-out canary slice; alert if any top-10 class drops more than 5 pp

5. **Cost analysis**
   - HF Space free tier: $0/month
   - Self-hosted on AWS c6i.xlarge: ~$0.17/hr, ~$120/month
   - Per-prediction cost on c6i.xlarge: ~$0.000005 (5 microdollars)
   - Per 1M predictions: < $5

6. **Rollback procedure**
   - Every model artifact has a `version` field in `meta.json`
   - Rollback = swap the joblib in `model_assets/` with the previous version + redeploy the Space
   - SQLite log preserves all prior predictions for audit

---

## 8. The architecture diagram (Codex generates)

Single matplotlib-produced PNG saved to `docs/architecture/system_diagram.png` and embedded in:
- The Methodology page of the frontend
- The HF Space Methodology tab
- Slide 5 of the final presentation
- The Deployment Runbook
- The Final Report

Spec is in `CODEX_BUILD_TASKS.md` Section 4. Use the navy/teal/coral/gold/sage palette. Horizontal flow. Two parallel pipelines (training above, inference below). 11×6 inches, 200 DPI.

---

## 9. The 12-slide presentation deck (Codex generates → Akash polishes)

| # | Slide title | Key content |
|---|---|---|
| 1 | GECS-Sage — Production-Ready Classification for Morningstar's GECS Taxonomy | Title card, team, partner, date |
| 2 | Executive summary | 4 KPI tiles: current honest F1, accuracy, top-10 pass count, median latency |
| 3 | The problem framing | 3 sectors / 11 sectors / 55 groups / 145 industries / 450 activities visual; class imbalance chart |
| 4 | The audit story | 88.90% → 60% → 69% (rebuilt) chart. **This slide opens the methodology section. Spend 90 seconds here.** |
| 5 | Architecture | Embed `system_diagram.png` |
| 6 | Methodology innovation | Show the GECS PDF anchor approach with a side-by-side: official definition vs sample prediction |
| 7 | Results | Final results table with Macro F1, accuracy, precision, recall, top-10 pass |
| 8 | Top-10 class performance | Per-class F1 bar chart highlighting the 31030010 conglomerate problem |
| 9 | Task 2 strategy | Hierarchical Task 1 → Task 2 constraint diagram |
| 10 | Live demo | Three screenshots: predict screen, low-confidence deferral, metrics dashboard |
| 11 | Production deployment | Docker, HF Space URL, latency benchmark, retraining cadence |
| 12 | Closing | The closing line verbatim from the Legendary Playbook. Audit-as-feature recap. |

Codex builds the deck skeleton with `python-pptx`. Akash adds the live URL, real numbers, and the demo screenshots after Wednesday's deploy.

---

## 10. README revamp (Codex writes the top-level `README.md`)

Required contents:

1. **Header** — `GECS-Sage v1.0` + tagline + badge row (Python 3.11, MIT license, build status)
2. **One-paragraph product description**
3. **Live demo link** to the HF Space (added after Wednesday deploy)
4. **Quick start** — three commands to run locally
5. **What makes this different** — the four differentiators bulleted (audit, GECS PDF, calibrated probabilities, analyst override)
6. **Architecture** — embed `system_diagram.png`
7. **Repo map** — tree-style overview
8. **Documentation** — links to `docs/Initial_Proposal_TAVSS.docx`, `CASCADE_AUDIT.md`, `PROJECT_JOURNEY.md`, `DEPLOYMENT_RUNBOOK.md`
9. **Team** — Akash + four teammates + Morningstar partnership credit
10. **License**

No emojis. Production project README, not a marketing page.

---

## 11. The full demo flow on Monday (lock this)

During the presentation, the demo cell runs in this exact order. Have it scripted. Don't improvise.

| t (min) | Action | What renders |
|---|---|---|
| 0:00 | Open the HF Space URL on the projector | The classifier home tab |
| 0:15 | Paste: *"Operates regional retail banks in the Midwest with ~50 branches focused on commercial lending."* | (typing happens live) |
| 0:30 | Click Classify | Loading state |
| 0:45 | Result renders | Task 1: 10320020 Banks — Regional @ 84%; Task 2: Commercial Lending @ 78%; official GECS definition quoted; alternatives panel; processing trace |
| 1:30 | Click "Show reasoning" | Reasoning trace expands |
| 2:30 | Paste: *"Diversified holding company operating in industrial manufacturing, energy infrastructure, and financial services."* | Low-confidence path renders |
| 3:00 | Coral warning shows: *"Low confidence — recommend analyst review."* | All 3 candidates shown |
| 3:30 | Switch to the Metrics tab | KPI tiles, latency histogram, top-predicted classes |
| 4:00 | Switch to the Methodology tab | The audit narrative + architecture diagram |
| 4:30 | Ask the Morningstar rep to type their own example | (interaction happens live) |
| 5:00 | Closing line, eye contact, sit down | Done. |

If the live HF Space is down at presentation time, you fall back to the local Flask + Next.js running on the laptop. Have both ready. **Test both on the morning of Monday May 18.**

---

## 12. Codex execution order for the system revamp

Hand Codex this exact sequence. **Calendar dates are relative — verify against your laptop calendar.**

### Codex priority hierarchy (read first)

If Codex falls behind schedule, **these three tasks are non-negotiable must-ships:**
- **Task A** — Backend patch (the API has to return real predictions)
- **Task D** — Frontend home page with prediction card (the screen Morningstar sees)
- **Task H** — HF Space scaffold + deploy (the live URL)

Everything else (history page, metrics page, methodology page, runbook, slides skeleton, README polish) is **important but cuttable to a skeleton** if Codex is behind. Polish what matters most: the live demo screen.

### Before Codex starts ANY task — house rules

> **Codex must do these three things before writing code on any task:**
> 1. Read the existing files in `frontend/`, `serve/`, and `legendary/` first. Do not delete or rewrite existing pages — add to or modify them.
> 2. Run the existing `server_legendary.py` first to surface any broken imports before adding new endpoints.
> 3. Read this `FULL_SYSTEM_REVAMP.md` and `HANDOFF_PLAYBOOK.md` in full before writing the first line of code on any task.

### Sequence

```
T+0 night
├── Task A: Backend patch       (Section 3 above + CODEX_BUILD_TASKS.md Task 1 revised)
└── Task B: System diagram       (CODEX_BUILD_TASKS.md Task 4)

T+1
├── Task C: LLM judge module     (CODEX_BUILD_TASKS.md Task 2) — laptop only, NOT for HF Space
├── Task D: Frontend index.tsx + components  (Section 2 above + CODEX_BUILD_TASKS.md Task 3)
└── Task E: README revamp        (Section 10 above)

T+2
├── Task F: Frontend history + metrics pages
├── Task G: Frontend methodology page (the audit story)
├── Task H: HF Space scaffold (Section 5 above) — Ollama imports MUST be conditional/absent
└── Task I: Deployment runbook draft

T+3  (Akash hands over model artifacts at start of day)
├── Task J: Wire model (ONNX-INT8 if available, else FP32 PyTorch) into HF Space app.py
├── Task K: Deploy to HF Space, get live URL
└── Task L: Deployment runbook final fill (with real latency numbers)

T+4
├── Task M: Slides deck via python-pptx (Section 9 above)
└── Task N: Polish + cross-page consistency

T+5  Available for fixes
```

### Deployment safety net

The HF Space deploy can fail on T+3 for many reasons: HF auth, file-size limits, dependency resolution, model loading errors. **Always have a working local demo (Flask backend + Next.js frontend on Akash's laptop) tested and ready as backup.** Test both flows the morning of T+7 before walking in.

Each task has its full spec in either this document or `CODEX_BUILD_TASKS.md`.

---

## 13. Things Codex must not do

- ❌ Rewrite `server_legendary.py` from scratch. Patch it.
- ❌ Introduce FastAPI. Keep Flask.
- ❌ Add ChatGPT API calls, OpenAI calls, or any paid API at inference time.
- ❌ Use placeholder data on the metrics page. Connect to the real SQLite log.
- ❌ Use stock photos or marketing illustrations. No "AI hand reaching toward brain" images.
- ❌ Add emojis to production UI surfaces.
- ❌ Use cute branding ("GECS-Sage 🧙"). No.
- ❌ Build a Streamlit dashboard. Stick to Next.js + Gradio.
- ❌ Skip the Methodology page. That page is the differentiation.

---

## 14. Final pre-submission checklist (Sunday May 17 night)

```
□ Live HF Space URL works on a phone
□ /health endpoint returns ok
□ /predict returns the full canonical schema
□ Three example chips load real predictions
□ Low-confidence example triggers the coral warning
□ Override button records to SQLite
□ Metrics page shows real numbers, not zeros
□ Methodology page tells the audit story
□ Architecture diagram embedded everywhere it's referenced
□ README revamped with the live URL filled in
□ Slides finalized with the real F1 numbers (not TBD)
□ Final Report consolidated
□ All weekly reports + Initial Proposal in /docs
□ GitHub repo public, weekly commits visible
□ Practice demo run timing < 5 minutes
□ Closing line memorized verbatim
□ Backup laptop demo tested
□ Sleep 8 hours before Monday
```

---

## 15. The single sentence to remember

> **"We didn't try to replace your analysts. We tried to build the tool we'd want as one of them."**

If everything else falls apart, deliver that sentence with the audit slide and the live URL, and you have a winning submission.

---

*Companion to `HANDOFF_PLAYBOOK.md` · Prepared May 11, 2026 · Submission deadline May 18, 2026*
*Akash Anipakalu Giridhar · Group 4 · DePaul University Chicago · MGT 599*
