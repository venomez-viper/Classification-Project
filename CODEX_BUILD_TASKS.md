# Codex Build Tasks — GECS-Sage Deployment System

**Project:** MGT 599 Capstone — Morningstar GECS Industry/Subindustry Classification
**Deadline:** Monday May 18, 2026
**Your job:** Build the deployment infrastructure (API, frontend, logging, runbook, slides).
**Akash's job:** Build the ML core (Task 2 classifier, distillation, model artifacts, eval).

---

## Repo state you can rely on

```
capstone MGT 599/
├── data/cleaned/task1_clean.csv           # 53,585 rows, columns: text, mstar_code, ...
├── data/cleaned/task2_clean.csv           # 27,537 rows
├── llm_finetuning/data/task1_train.csv    # 42,868 rows for training
├── llm_finetuning/data/task1_test.csv     # 10,717 rows for held-out eval
├── gecs_taxonomy.json                     # 145 GECS codes with sector_name, industry_name, description, label_text
├── models_v10/                            # Akash will provide the final calibrated joblib here
│   └── v10_calibrated.joblib              # CalibratedClassifierCV pickled
├── models_v13/v13_*.joblib                # GECS-anchor model artifacts (existing)
├── models_task2/                          # Akash will provide
│   ├── task2_classifier.joblib            # Task 2 model
│   └── task1_to_task2_map.json            # deterministic mapping
├── server_legendary.py                    # ← BROKEN, do not extend. Replace with new FastAPI server.
├── frontend/                              # Existing React app (Next.js)
├── docs/proposal_exhibits/                # PNG charts already produced
└── CASCADE_AUDIT.md, PROJECT_JOURNEY.md   # Existing audit docs
```

---

# TASK 1 — Build the FastAPI server

**File:** `serve/app.py` (new)
**Dependencies to add to `requirements.txt`:** `fastapi`, `uvicorn[standard]`, `joblib`, `pydantic>=2`, `sqlalchemy`, `ollama-python` (optional)
**Acceptance:** `uvicorn serve.app:app --host 0.0.0.0 --port 5003` starts cleanly, `/docs` shows OpenAPI UI, `/predict` returns valid JSON.

## API contract

```
POST /predict
Request:
{
  "company_text": "string — segment description or full company text",
  "include_reasoning": true   // optional, default false
}

Response (200):
{
  "task1": {
    "code": "10320020",
    "industry_name": "Banks—Regional",
    "sector_name": "Financial Services",
    "confidence": 0.84,
    "official_definition": "Regional, diverse financial institutions...",
    "matched_phrase": "regional retail banking"     // top matching span
  },
  "task2": {
    "code": "10320020-02",
    "subindustry_name": "Commercial Lending",
    "confidence": 0.78,
    "constrained_by_task1": true
  },
  "alternatives": [
    {"code": "10320010", "industry_name": "Banks—Diversified", "confidence": 0.09, "rejection_reason": "no global scope cited"},
    {"code": "10360010", "industry_name": "Credit Services",   "confidence": 0.03, "rejection_reason": "..."}
  ],
  "reasoning": "Optional LLM reasoning trace if include_reasoning=true",
  "trace": {
    "tfidf_ms": 18,
    "retrieval_ms": 22,
    "classifier_ms": 5,
    "task2_ms": 3,
    "llm_judge_ms": 0,
    "total_ms": 48
  },
  "model_version": "v1.0",
  "prediction_id": "uuid4"
}

GET /health        → 200 OK with model version
GET /metrics       → prediction count, latency p50/p95/p99, confidence histogram
GET /history?limit=50  → last N predictions from SQLite log
GET /docs          → OpenAPI auto-generated UI
```

## Codex prompt for this task

> Build a FastAPI application at `serve/app.py` for serving a GECS industry/subindustry classifier. The app must:
> - Load `models_v10/v10_calibrated.joblib` (a `CalibratedClassifierCV` wrapping a LinearSVC), `models_task2/task2_classifier.joblib`, `models_task2/task1_to_task2_map.json`, and `gecs_taxonomy.json` (a list of dicts with keys `mstar_code`, `sector_name`, `industry_name`, `description`) at startup.
> - Expose `POST /predict` with the request/response schema in the spec above. Predictions return Task 1 code + Task 2 code (using the deterministic mapping as a hard constraint — restrict Task 2 candidates to those whose parent industry equals the predicted Task 1 code).
> - Compute latency for each stage and return it in the `trace` field.
> - Log every prediction to a SQLite DB at `serve/predictions.sqlite` with columns: id (uuid), timestamp, input_text, task1_code, task1_confidence, task2_code, task2_confidence, model_version, latency_ms.
> - Expose `GET /metrics` aggregating: total predictions, latency p50/p95/p99 from the SQLite log, confidence histogram (10 buckets).
> - Expose `GET /health` returning `{"status": "ok", "model_version": "v1.0", "models_loaded": true}`.
> - Use Pydantic v2 for request/response validation.
> - Add CORS middleware for the frontend on `http://localhost:3000`.
> - Use Python type hints throughout. No fake confidence — only `clf.predict_proba()` outputs.

---

# TASK 2 — Optional LLM Judge stage (Ollama)

**File:** `serve/llm_judge.py` (new)
**Dependencies:** `ollama` Python client; user has Ollama installed locally with `qwen2.5:3b-instruct` pulled.
**Acceptance:** Called by `/predict` when `top1_confidence < 0.7`. Returns chosen code + reasoning string in < 5 seconds.

## Contract

```python
def llm_judge(
    company_text: str,
    top_k_candidates: list[dict],       # [{code, industry_name, description, sklearn_proba}, ...]
    timeout_s: float = 5.0,
) -> dict:
    """Returns {'chosen_code': '10320020', 'reasoning': '...', 'rejected': [...]}.
    Falls back to top-1 candidate if Ollama is unreachable.
    """
```

## Codex prompt

> Implement `serve/llm_judge.py` with one function `llm_judge(company_text, top_k_candidates, timeout_s)` that:
> - Builds a chain-of-thought prompt presenting the company text and 3-5 candidate GECS codes with their official descriptions.
> - Calls a local Ollama model (`qwen2.5:3b-instruct` by default; configurable via env var `OLLAMA_MODEL`) using the `ollama` Python client.
> - Asks the model to reason step-by-step and end with `FINAL_CODE: <8-digit>` and a short rejection reason per non-chosen candidate.
> - Parses the response and returns `{chosen_code, reasoning, rejected: [{code, reason}, ...]}`.
> - Wraps the call in a timeout (`asyncio.wait_for` with `timeout_s`). On timeout or any exception, falls back to the highest-`sklearn_proba` candidate and sets `reasoning = "LLM judge unavailable; using classifier top-1."`
> - Includes a `if __name__ == "__main__"` smoke test that hits Ollama with a hard-coded example.

---

# TASK 3 — Frontend updates

**Folder:** `frontend/` (existing Next.js + Tailwind)
**Acceptance:** Running `npm run dev` shows the new UI; backend connection works; sample prediction renders correctly.

## Pages to update / add

### `frontend/pages/index.tsx` — main demo screen

Layout:
```
┌─────────────────────────────────────────────────────────┐
│  GECS-Sage  ·  Industry & Subindustry Classifier        │
├─────────────────────────────────────────────────────────┤
│  [ Large text area for company description ]            │
│  [ Classify ] button                                    │
├─────────────────────────────────────────────────────────┤
│  PRIMARY PREDICTION                                     │
│  Task 1: 10320020 · Banks—Regional          ●●●●○ 84%  │
│  Task 2: 10320020-02 · Commercial Lending   ●●●●○ 78%  │
├─────────────────────────────────────────────────────────┤
│  Official GECS Definition (Morningstar 2019)            │
│  "Regional, diverse financial institutions..."          │
│  ▸ Matched phrase: "regional retail banking"            │
├─────────────────────────────────────────────────────────┤
│  Top-3 Alternatives                                     │
│   ○ 10320010 Banks—Diversified  9%   (rejected: ...)    │
│   ○ 10360010 Credit Services    3%   (rejected: ...)    │
├─────────────────────────────────────────────────────────┤
│  Processing trace (collapsible)                         │
│   ▸ TF-IDF + multi-encoder retrieval  18 ms             │
│   ▸ RAG over 145 GECS definitions     22 ms             │
│   ▸ Calibrated probability head        5 ms             │
│   ▸ Hierarchical Task 2 constraint     3 ms             │
│   ▸ Total                             48 ms             │
├─────────────────────────────────────────────────────────┤
│  [ Accept ]  [ Override ]  [ Flag for review ]          │
└─────────────────────────────────────────────────────────┘
```

### `frontend/pages/history.tsx` — recent predictions table
Columns: timestamp, input excerpt, predicted Task 1, predicted Task 2, confidence, status (accepted/overridden/flagged).

### `frontend/pages/metrics.tsx` — dashboard
Show: total predictions, latency histogram, confidence distribution, top predicted classes.

## Codex prompt

> Update the existing Next.js app in `frontend/` to add three pages:
>
> **`pages/index.tsx`** — main classification UI. Single text area, "Classify" button. On submit, POST to `http://localhost:5003/predict` with `{company_text, include_reasoning: true}`. Render the response per the layout in the spec above. Use Tailwind for styling, with a navy/teal color palette (Tailwind classes `bg-slate-900`, `text-teal-400`, `border-amber-400`). Show real confidence bars using `clf.predict_proba` values (no fake softmax). Show the matched GECS definition phrase highlighted. Display top-3 alternatives with rejection reasons. Collapsible "Processing trace" section showing latency per stage. Three buttons at bottom: Accept (POST `/feedback`), Override (open dropdown of 145 codes), Flag for review (POST `/feedback` with status='flagged').
>
> **`pages/history.tsx`** — fetch `GET /history?limit=50` and render a sortable table.
>
> **`pages/metrics.tsx`** — fetch `GET /metrics` and render KPI tiles + a simple bar chart of latency p50/p95/p99 using `recharts`.
>
> Add a top-bar nav linking to Home / History / Metrics. Use the existing `_app.tsx` layout. Make it look like a Morningstar internal tool — clean, dense, professional. No emojis. No marketing fluff.

---

# TASK 4 — Architecture diagram for the slides

**File:** `docs/architecture/system_diagram.png` (new) + source `docs/architecture/system_diagram.py`
**Acceptance:** A clean publication-quality PNG showing the full inference pipeline.

## Spec

A horizontal flow diagram showing:
```
[User input] →
[Multi-encoder feature stack: TF-IDF + MiniLM + BGE] →
[RAG over GECS taxonomy (145 anchor definitions)] →
[Calibrated LinearSVC head (BreezeML)] →
[Hierarchical Task 1→Task 2 constraint] →
[Optional Qwen2.5 LLM judge for low-confidence] →
[Top-3 + reasoning + analyst override]
```

Plus a separate offline training flow:
```
[task1_train.csv] → [BreezeML training pipeline] → [models_v10/]
[GECS PDF] → [scripts/parse_gecs_taxonomy.py] → [gecs_taxonomy.json]
```

## Codex prompt

> Write `docs/architecture/system_diagram.py` using `matplotlib.patches.FancyBboxPatch` and `FancyArrowPatch` to produce a clean horizontal system diagram. Save to `docs/architecture/system_diagram.png` at 200 DPI. Use the McKinsey-ish palette: navy (#1F3A5F), teal (#0E6B6E), coral (#E07856), gold (#D4A93F), sage (#7A9E7E). Inference pipeline runs left-to-right at y=4. Offline training pipeline runs left-to-right at y=1 in lighter colors. Add a title bar at top: "GECS-Sage v1.0 · Inference & Training Architecture." Each box has a title in bold + one-line subtitle. Arrows between boxes are simple curved lines. The output file is the spec — the script should run end-to-end and produce a 11x6 inch PNG.

---

# TASK 5 — Deployment runbook

**File:** `docs/DEPLOYMENT_RUNBOOK.md` (new)
**Acceptance:** A reader who has never seen the project can clone, set up, and run the system in 10 minutes.

## Contents required

1. **Prerequisites:** Python 3.11, Node.js 20, optional Ollama with qwen2.5:3b-instruct
2. **Install:** `pip install -r requirements.txt`, `cd frontend && npm install`
3. **Run locally:**
   - Backend: `uvicorn serve.app:app --host 0.0.0.0 --port 5003`
   - Frontend: `cd frontend && npm run dev` (port 3000)
   - Optional LLM judge: `ollama serve` and pull `qwen2.5:3b-instruct`
4. **Smoke test:** `curl -X POST http://localhost:5003/predict -H 'Content-Type: application/json' -d '{"company_text": "Regional bank serving Midwest commercial customers"}'`
5. **Deployment options:**
   - Single CPU box (recommended for Morningstar RED): describe RAM/CPU footprint
   - Docker (write the Dockerfile)
   - Kubernetes (Helm chart skeleton — optional, time permitting)
6. **Retraining:**
   - When a new GECS code is added: update `gecs_taxonomy.json`, retrain V10
   - Monthly cadence: `python scripts/train_cascade_v10.py`
   - Cost: ~10 min on a 4-core CPU
7. **Drift monitoring:**
   - SQLite log analyzed weekly
   - Alert if confidence drops more than 5pp on top-10 classes
8. **Rollback procedure:** how to revert to a prior model artifact
9. **Cost analysis:** estimated ms/prediction, predictions/second, $/1M predictions on AWS c6i.xlarge

## Codex prompt

> Write `docs/DEPLOYMENT_RUNBOOK.md` covering the 9 sections above. Be specific about commands (every command must be runnable). Include a Dockerfile in section 5 that builds a runnable image (python:3.11-slim base, copy serve/, install requirements, EXPOSE 5003, CMD uvicorn). Include a benchmark table in section 9 (rows: latency p50, p95, p99; throughput requests/sec; memory peak; cost per 1M predictions on c6i.xlarge at $0.17/hr). Use real values from `GET /metrics` once Akash has wired the backend.

---

# TASK 6 — Slides (10-12 slides)

**File:** `docs/presentation/GECS_Sage_Final.pptx` (new) + source `docs/presentation/build_slides.py`
**Acceptance:** Slides render cleanly in PowerPoint and tell the full story in 10-12 minutes.

## Slide outline

1. **Title** — "GECS-Sage: Production-Ready Industry & Subindustry Classification"
2. **Executive summary** — 4 KPI tiles (current F1, accuracy, top-10 pass, latency)
3. **The problem** — 145 industries, 450 subindustries, hierarchical, long-tail
4. **The audit story** — 88.90% leaked → 69.09% honest. *This is the slide that wins respect.*
5. **Architecture diagram** — embed `system_diagram.png`
6. **Methodology innovation** — GECS PDF anchoring (only team that did this)
7. **Results table** — V1–V20 progression
8. **Top-10 class performance** — embed `exhibit_3_top10_breakdown.png`
9. **Task 2 strategy** — hierarchical constraint diagram
10. **Live demo screenshots** — 3 screens
11. **Production deployment** — Docker, latency benchmark, retraining cadence
12. **Closing** — "The number is real. The system is deployable."

## Codex prompt

> Write `docs/presentation/build_slides.py` using `python-pptx` to build a 12-slide deck per the outline. Match the McKinsey navy/teal palette from `docs/proposal_exhibits/`. Each slide has a slide title at the top (navy, 28pt) and supporting bullets / images below. Embed the existing PNG exhibits from `docs/proposal_exhibits/` where indicated. Slide 10 (live demo) should have placeholder image boxes labeled "screenshot to be added by Akash before submission." Save to `docs/presentation/GECS_Sage_Final.pptx`.

---

# TASK 7 — README polish for the GitHub repo

**File:** `README.md` (top of repo, overwrite existing if any)
**Acceptance:** Anyone landing on the repo understands the project, runs it in 10 min, and finds the audit story.

## Contents

```markdown
# GECS-Sage

Production-ready industry and subindustry classification for Morningstar's GECS
taxonomy — built around honest evaluation, the regulator's own taxonomy
document, and a deployable analyst-in-the-loop workflow.

## Current status
| Metric | Value |
|---|---|
| Task 1 Macro F1 (honest) | 69.09% |
| Task 1 Accuracy | 71.65% |
| Task 2 Macro F1 | (TBD) |
| Median inference latency | (TBD ms) on CPU |

## Quick start
[install + run commands]

## What makes this different
1. Caught a 30-point data leakage in our own baseline (see CASCADE_AUDIT.md)
2. Parsed all 145 official GECS definitions from the Morningstar 2019 PDF
3. RAG-style retrieval grounds every prediction in the regulator's text
4. Calibrated probabilities — no fake softmax
5. Analyst-override workflow in the UI

## Repo map
[tree-style overview]

## Docs
- [Initial Proposal](docs/Initial_Proposal_TAVSS.docx)
- [Deployment Runbook](docs/DEPLOYMENT_RUNBOOK.md)
- [Leakage Audit](CASCADE_AUDIT.md)
- [Project Journey](PROJECT_JOURNEY.md)
```

## Codex prompt

> Overwrite the existing `README.md` at the repo root with a production-grade README per the spec above. Include a badge row (Python version, license MIT, last commit). Tree-style repo map showing serve/, frontend/, scripts/, models_v10/, models_task2/, docs/, data/. Reference all existing docs by relative path. Don't invent metrics — leave TBDs for Task 2 F1 and latency until Akash provides numbers.

---

# What Akash is building in parallel (do NOT touch these)

| File | What I'm doing |
|---|---|
| `scripts/build_task2_classifier.py` | Task 2 classifier with deterministic Task 1 → Task 2 constraint |
| `models_v10/v10_calibrated.joblib` | Calibrated probability wrapper around V10 |
| `models_task2/task2_classifier.joblib` | Trained Task 2 model |
| `models_task2/task1_to_task2_map.json` | The deterministic mapping |
| `colab/distill_step1_*.ipynb` etc. | Distillation pipeline (Mon–Tue) |
| `scripts/evaluate_final.py` | Final F1/precision/recall/top-10 on `task1_test.csv` |

**Once these are saved to the right paths, your FastAPI app will pick them up at startup.**

---

# Suggested execution order (Codex builds in this order)

```
SUN night (tonight)
├── Task 1  FastAPI server skeleton + SQLite logger
└── Task 4  Architecture diagram

MON
├── Task 2  LLM judge module (depends on Ollama running locally)
├── Task 3  Frontend index.tsx update
└── Task 7  README

TUE
├── Task 3  Frontend history.tsx + metrics.tsx
└── Task 5  Deployment runbook (skeleton with placeholders)

WED
├── Task 5  Deployment runbook (fill in real latency numbers from /metrics)
└── Task 6  Slides

THU
└── Polish + dry run
```

---

# Hand-off protocol

When you finish a Codex task:
1. Commit to a new branch `codex/task-N-<name>` in the repo.
2. Open a pull request with the diff visible.
3. Drop a one-line summary in the project Slack: "Task N done, ready for Akash to wire."
4. Wait for green light before merging if your task depends on an artifact Akash hasn't produced yet.

---

# What I (Akash) am owning end-to-end

- The actual ML model and its eval numbers
- The distillation pipeline (Monday–Tuesday on Colab)
- The CASCADE_AUDIT.md and PROJECT_JOURNEY.md content
- The Initial Proposal and Week 5 Report (already done)
- The live demo content / sample queries

**You build the rails. I produce the train.**

---

*Doc prepared: May 11, 2026 · Submission deadline: May 18, 2026*
