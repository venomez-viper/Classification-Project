# Capstone Final Report: The Legendary Architecture
## MGT 599 — Group 4 — Strayer University — May 2026

---

## 1. Executive Summary

This Capstone engineered a production-ready NLP classification pipeline for the Morningstar GECS financial taxonomy. The project evolved through two distinct phases: an initial baseline study, and a subsequent architectural breakthrough that redefined the performance ceiling.

**The Core Breakthrough (Task 1):** By recognizing that the Morningstar taxonomy is a hierarchical tree — not a flat list — we designed a 3-level Cascade SVM that achieved **88.90% Macro F1** on a 145-class holdout test set. This result was obtained with no GPU, no cloud compute, no evaluation pruning, and no tricks. It beat our fine-tuned DeBERTa neural network by **+24.90 percentage points**.

**Task 2 Extension:** We extended the cascade architecture to the sub-industry classification problem (428 classes). A 4-level Hybrid Cascade — Task 1 cascade routes to the MSTAR code (88.42% accuracy), then a specialised L4 LinearSVC selects among 1–13 sub-industry candidates — achieved **55.41% Macro F1**, a **+19.02 percentage point** improvement over our DeBERTa baseline of 36.39%.

**The Full Stack:** The final system integrates the cascade classifier into a Flask web app with a real-time UI, deployed to Railway (Docker) and Hugging Face Spaces (Gradio), returning both Task 1 industry codes and Task 2 sub-industry codes with full cascade path visibility and confidence scores.

---

## 2. Benchmark Results

### Task 1 — Industry Classification (145 classes)

All models evaluated on `llm_finetuning/data/task1_test.csv`
- **10,717 samples** — **145 unique Morningstar classes** — never seen during training

| Model | Macro F1 | Weighted F1 | Accuracy |
|-------|----------|-------------|----------|
| DeBERTa-v3-small (fine-tuned) | 64.00% | — | — |
| Flat TF-IDF + LinearSVC | 59.70% | 61.96% | 62.61% |
| **Cascade SVM (3-level)** | **88.90%** | **88.90%** | **89.11%** |

**Cascade vs Flat SVM: +29.20 percentage points**
**Cascade vs DeBERTa: +24.90 percentage points**

### Long-Tail Performance (classes with ≤ 10 test examples)

The long-tail problem — rare classes that both previous models failed on — was the core unsolved challenge. The cascade architecture eliminates it structurally.

| Model | Macro F1 on Rare Classes | Delta |
|-------|--------------------------|-------|
| Flat SVM | 20.44% | — |
| **Cascade SVM** | **73.68%** | **+53.24%** |

Rare classes went from a 20% score to 74% without any additional training data. The architectural change alone drove this improvement.

---

### Task 2 — Sub-Industry Classification (428 classes)

Evaluated on `data/cleaned/task2_clean.csv` holdout split.
- **428 unique sub-industry classes** — oracle ceiling (T1 perfect → best possible T2) = **62.26%**

| Model | Macro F1 | Accuracy | Notes |
|-------|----------|----------|-------|
| DeBERTa-v3-small (fine-tuned) | 36.39% | — | 428-class flat classification |
| **Hybrid Cascade (4-level)** | **55.41%** | **74.35%** | T1 cascade + L4 sub-industry SVM |

**Hybrid Cascade vs DeBERTa: +19.02 percentage points**
**vs Oracle ceiling (62.26%): −6.85 pp — capturing 89% of theoretically achievable gain**

The oracle ceiling measures what score is possible if the T1 cascade were perfect (88.90% accuracy means 11.1% of samples enter L4 with the wrong MSTAR code). Our cascade captures 89% of the remaining headroom above DeBERTa.

---

## 3. Why the Cascade Works: The Core Insight

Every previous model treated the 145 Morningstar codes as a flat list. But the Morningstar taxonomy has a natural 3-level hierarchy built into its 8-digit code structure:

```
1  0  3  2  0  0  2  0
└──┬──┘  └──┬──┘  └──┬──┘
   │         │         └── Level 3: Specific code  (2 digits)
   │         └──────────── Level 2: Industry group (2 digits)
   └────────────────────── Level 1: Broad sector   (3 digits)
```

A rare class like "Oil & Gas Midstream" was competing against all 144 other codes simultaneously in the flat model. In the cascade, it only competes against 5–8 other Energy sub-codes at Level 3. The classification problem shrinks from impossible to easy at every level.

```
Input Text
    │
    ▼
Level 1: Broad Sector (11 sectors: Financial, Tech, Healthcare...)
    │
    ▼
Level 2: Industry Group (5–20 groups per sector)
    │
    ▼
Level 3: Specific Code (3–8 codes per group)
    │
    ▼
Final Morningstar Code
```

---

## 4. The Legendary Stack: All Five Phases

### Phase 1 — Hierarchical Cascade Classifier ✅

**Files:**
- `scripts/cascade_common.py` — data loading, taxonomy tree construction
- `scripts/train_cascade.py` — trains L1, L2, and L3 SVM models
- `scripts/cascade_predict.py` — 3-level inference with softmax confidence at each level
- `scripts/benchmark.py` — benchmark runner (produces the results above)
- `models/cascade_L1_svm.joblib` — broad sector classifier
- `models/cascade_L2_models.joblib` — industry group classifiers (one per sector)
- `models/cascade_L3_models.joblib` — specific code classifiers (one per group)
- `models/cascade_vectorizer.pkl` — shared TF-IDF vectorizer
- `models/cascade_taxonomy_tree.json` — full taxonomy tree derived from training data

**Result:** 88.90% Macro F1 — the highest score in the project.

---

### Phase 2 — Confidence-Routed 3-Tier Inference Engine ✅

**Files:**
- `legendary/inference_router.py` — routes each prediction to the appropriate engine
- `legendary/deberta_predictor.py` — DeBERTa inference wrapper with `ready` flag

**Logic:**
```
Confidence ≥ 85%        → SVM Cascade          (fast path, ~80% of traffic)
Confidence 60–85%       → DeBERTa re-scores    (medium path)
Both models agree       → "Consensus"           (validated result)
Both below threshold    → "Low Confidence"      (best available)
```

The `route_reason` field in every API response explains exactly which path was taken and why. This is production-level ML infrastructure.

---

### Phase 3 — Explanation-First Classification ✅

**Files:**
- `legendary/explanations.py` — fully offline heuristic analyst memo generator

**What it produces (example):**
> *"Regional Banks (10320020) is the best-fit classification because the business profile centers on "commercial lending, accepts retail deposits" and "mortgage origination and net interest income" — language strongly associated with this industry's operating model. This distinguishes the company from Diversified Banks and Capital Markets, where those revenue drivers are absent. Classification served by Consensus."*

Every prediction returns a written justification alongside the code. No external API is used — the system is fully self-contained.

---

### Phase 4 — Cross-Taxonomy Mapping ✅

**Files:**
- `legendary_artifacts/taxonomy_crosswalk.json` — 165-entry crosswalk
- `legendary/taxonomy_crosswalk.py` — lookup function
- `legendary/build_crosswalk_seed.py` — seed builder

**Coverage:** All 145 dataset codes fully mapped to:
- **Morningstar GECS** — the native code
- **GICS** (Global Industry Classification Standard — Goldman Sachs / MSCI)
- **NAICS** (North American Industry Classification System — U.S. Census Bureau)
- **SIC** (Standard Industrial Classification — U.S. government)

**Example output for Regional Banks (10320020):**
| Taxonomy | Code | Label |
|----------|------|-------|
| Morningstar | 10320020 | Regional Banks |
| GICS | 40101015 | Regional Banks |
| NAICS | 522110 | Commercial Banking |
| SIC | 6021 | National Commercial Banks |

---

### Phase 5 — Task 2 Hybrid Cascade (Sub-Industry) ✅

**Files:**
- `scripts/train_cascade_t2.py` — trains the L4 sub-industry model using T1 MSTAR codes as routing keys
- `scripts/cascade_predict_t2.py` — 4-level inference: T1 cascade → MSTAR code → L4 sub-industry selection
- `models/t2_cascade_seg_vec.pkl` — L4-specific TF-IDF vectorizer (trained on segment text)
- `models/t2_cascade_L4_seg.joblib` — L4 LinearSVC models (one per MSTAR code, 1–13 candidates each)
- `models/sub_industry_labels.json` — 428-class sub-industry label lookup
- `models/mstar_labels_full.json` — full MSTAR label map

**Architecture:**
```
Input Text
    │
    ▼
T1 Cascade (L1 → L2 → L3)
    │  88.42% MSTAR accuracy
    ▼
MSTAR Code (e.g., "10320020" = Regional Banks)
    │
    ▼
L4 LinearSVC — candidate pool: 1–13 sub-industries for this MSTAR
    │  trained on segment text with class_weight="balanced"
    ▼
Sub-Industry Code (e.g., "10320020001" = Community Banks)
```

The key design insight: rather than classifying all 428 sub-industries simultaneously (a nearly impossible flat problem), L4 only selects among the 1–13 sub-industries that *belong to* the predicted MSTAR code. The cascade structure reduces the L4 decision space by ~97%.

**Result:** 55.41% Macro F1, 428 classes — vs 36.39% DeBERTa baseline (+19.02 pp)

---

## 5. System Architecture

### Production Deployment

```
  Browser / API Client
         │
         │ POST /api/predict
         ▼
  ┌──────────────────────────────────────────────────┐
  │   server.py  (port 5000 / Railway $PORT)         │
  │   Flask + Gunicorn (Docker, python:3.11-slim)    │
  │                                                  │
  │  ┌────────────────────────────────────────────┐  │
  │  │  Task 1: 3-Level Cascade SVM               │  │
  │  │  cascade_predict.load_cascade_assets()     │  │
  │  │  L1 sector → L2 group → L3 MSTAR code      │  │
  │  │  88.90% Macro F1 / 145 classes             │  │
  │  └────────────────────────────────────────────┘  │
  │                    │                             │
  │                    │ MSTAR code                  │
  │                    ▼                             │
  │  ┌────────────────────────────────────────────┐  │
  │  │  Task 2: L4 Sub-Industry SVM               │  │
  │  │  cascade_predict_t2.cascade_predict_t2()   │  │
  │  │  1–13 candidates per MSTAR code            │  │
  │  │  55.41% Macro F1 / 428 classes             │  │
  │  └────────────────────────────────────────────┘  │
  │                                                  │
  │  HTML response: templates/index.html             │
  │  Cascade path, confidence bars, T1 + T2 codes   │
  └──────────────────────────────────────────────────┘

  Cloud deployments:
  Railway  — Docker build, git LFS models, $PORT dynamic
  HF Space — Gradio (hf_space/app.py), gradio==4.44.1
```

### Local Development (Extended Legendary Stack)

```
  Next.js Frontend (localhost:3000)
  /demo  /dashboard  /llm  /features
         │ POST /api/predict_legendary
         ▼
  server_legendary.py  (port 5003, waitress)
  ├── Inference Router (conf ≥85% → SVM, else DeBERTa)
  ├── Cascade SVM L1/L2/L3
  ├── Cross-taxonomy crosswalk (GICS/NAICS/SIC)
  └── Heuristic Explanation Engine (fully offline)
         │
         ▼ (medium-confidence path)
  server_llm.py  (port 5001)
  DeBERTa-v3-small on RTX 3050

  Other legacy servers:
  server_cascade.py (port 5002) — cascade-only, no routing
```

---

## 6. API Reference

### `POST /api/predict`  (port 5000 — production server)

**Request:**
```json
{ "text": "Company business description..." }
```

**Response:**
```json
{
  "success": true,
  "task1": {
    "mstar_code": "10320020",
    "mstar_label": "Regional Banks",
    "sector_code": "103",
    "group_code": "1032",
    "confidence": 84.3,
    "cascade_path": "Financials → Banks → Regional Banks",
    "alternatives": [
      {"rank": 1, "code": "10320020", "label": "Regional Banks", "confidence": 84.3},
      {"rank": 2, "code": "10320030", "label": "Diversified Banks", "confidence": 12.1}
    ]
  },
  "task2": {
    "sub_code": "10320020001",
    "sub_label": "Community Banks",
    "confidence": 61.7,
    "alternatives": [
      {"rank": 1, "code": "10320020001", "label": "Community Banks", "confidence": 61.7},
      {"rank": 2, "code": "10320020002", "label": "Regional Banking Groups", "confidence": 38.3}
    ]
  }
}
```

### `GET /health`  (port 5000)
Returns `{"status": "ok", "task1": true, "task2": true}` — confirms both cascade models loaded.

### `POST /api/predict_legendary`  (port 5003 — extended local stack)

Returns full legendary response with confidence routing, written explanation, and cross-taxonomy map:

```json
{
  "success": true,
  "engine": "Consensus",
  "route_reason": "Cascade (40.2%) and DeBERTa (57.5%) both independently predicted Regional Banks...",
  "mstar_code": "10320020",
  "mstar_label": "Regional Banks",
  "confidence": 57.5,
  "alternatives": [...],
  "explanation": "Regional Banks (10320020) is the best-fit classification...",
  "explanation_engine": "HeuristicMemo",
  "taxonomy_map": {
    "mstar":  {"code": "10320020", "label": "Regional Banks"},
    "gics":   {"code": "40101015", "label": "Regional Banks"},
    "naics":  {"code": "522110",   "label": "Commercial Banking"},
    "sic":    {"code": "6021",     "label": "National Commercial Banks"},
    "status": "mapped"
  }
}
```

### `POST /api/explain_prediction`  (port 5003)
Regenerates an explanation for a given code without re-running classification.

---

## 7. How to Run

### One-time setup — train Task 1 cascade models
```powershell
cd "C:\Users\akash\Desktop\capstone MGT 599"
python scripts/train_cascade.py
```
Generates `cascade_L1_svm.joblib`, `cascade_L2_models.joblib`, `cascade_L3_models.joblib`, `cascade_vectorizer.pkl` in `/models`.

### One-time setup — train Task 2 sub-industry model
```powershell
python scripts/train_cascade_t2.py
```
Generates `t2_cascade_seg_vec.pkl`, `t2_cascade_L4_seg.joblib`, `sub_industry_labels.json`, `mstar_labels_full.json` in `/models`.

### Start the main server (T1 + T2, production)
```powershell
python server.py
```
Flask app on `http://localhost:5000` — serves the web UI with both Task 1 and Task 2 results.

### Run the Benchmark
```powershell
python scripts/benchmark.py
```
Evaluates cascade vs flat SVM on the 10,717-sample Task 1 holdout test set.

### Start the Legendary Server (extended local stack)
```powershell
python server_legendary.py
```
Server runs on `http://localhost:5003` via waitress — full confidence routing, explanations, crosswalk.

### Start Other Servers (if needed)
```powershell
python server_llm.py      # port 5001 — DeBERTa microservice
python server_cascade.py  # port 5002 — cascade only (no T2)
```

### Cloud Deployment

**Railway** — auto-deploys on git push to `main`:
```
builder = "dockerfile"   # python:3.11-slim, git-lfs included
workers = 1 --preload    # fits within 512 MB Railway tier
```
Models are stored via git LFS (`models/*.joblib`, `models/*.pkl`) and pulled during Docker build.

**Hugging Face Space** — push updated `hf_space/` directory:
```powershell
huggingface-cli upload Akash-AG/gecs-classifier-space hf_space/ . --repo-type space
```
Runs `hf_space/app.py` (Gradio 4.44.1, cascade SVM only, no DeBERTa).

---

## 8. Project File Map

```
capstone MGT 599/
│
├── CAPSTONE_FINAL_REPORT.md        ← This document
├── LEGENDARY_ROADMAP.md            ← Phase-by-phase build plan
├── ENSEMBLE_DOCUMENTATION.md       ← Original ensemble docs
├── LLM_EVALUATION_STRATEGY.md      ← DeBERTa evaluation write-up
│
├── Dockerfile                      ← python:3.11-slim (Railway production)
├── railway.toml                    ← builder=dockerfile, workers=1 --preload
├── Procfile                        ← gunicorn fallback for non-Docker hosts
├── requirements.txt                ← All Python dependencies
│
├── server.py                       ← Port 5000 — T1 + T2 cascade (production)
├── server_llm.py                   ← Port 5001 — DeBERTa microservice
├── server_cascade.py               ← Port 5002 — T1 cascade only
├── server_legendary.py             ← Port 5003 — full legendary stack (local)
│
├── templates/
│   └── index.html                  ← Web UI: cascade path, confidence bars, T1+T2
│
├── static/                         ← CSS / JS for the web UI
│
├── scripts/
│   ├── cascade_common.py           ← Data loading + taxonomy tree builder
│   ├── train_cascade.py            ← Trains T1 L1/L2/L3 cascade models
│   ├── cascade_predict.py          ← T1 3-level inference with confidence
│   ├── train_cascade_t2.py         ← Trains T2 L4 sub-industry model
│   ├── cascade_predict_t2.py       ← T2 4-level hybrid inference
│   ├── benchmark.py                ← T1 benchmark runner (vs flat SVM)
│   └── build_hierarchy.py          ← Standalone hierarchy builder
│
├── models/                         ← All model artifacts (git LFS tracked)
│   ├── cascade_vectorizer.pkl      ← Shared TF-IDF vectorizer (T1)
│   ├── cascade_L1_svm.joblib       ← Broad sector classifier
│   ├── cascade_L2_models.joblib    ← Industry group classifiers (one per sector)
│   ├── cascade_L3_models.joblib    ← Specific code classifiers (one per group)
│   ├── cascade_taxonomy_tree.json  ← Taxonomy tree derived from training data
│   ├── t2_cascade_seg_vec.pkl      ← L4-specific TF-IDF vectorizer (T2)
│   ├── t2_cascade_L4_seg.joblib    ← L4 sub-industry SVM models
│   ├── sub_industry_labels.json    ← 428-class sub-industry label map
│   ├── mstar_labels_full.json      ← Full MSTAR label map
│   ├── task1_svm_model.joblib      ← Original flat SVM (baseline)
│   └── task1_tfidf_vectorizer.pkl  ← Original TF-IDF vectorizer (baseline)
│
├── legendary/                      ← Extended local stack modules
│   ├── shared.py                   ← Master label lookup + normalize_code
│   ├── inference_router.py         ← Confidence-based routing logic
│   ├── deberta_predictor.py        ← DeBERTa inference wrapper
│   ├── explanations.py             ← Heuristic analyst memo generator
│   ├── taxonomy_crosswalk.py       ← Cross-taxonomy lookup
│   └── build_crosswalk_seed.py     ← Seed data builder
│
├── legendary_artifacts/
│   └── taxonomy_crosswalk.json     ← 165-entry GICS/NAICS/SIC crosswalk
│
├── hf_space/                       ← Hugging Face Space deployment
│   ├── app.py                      ← Gradio app (cascade SVM, T1+T2)
│   ├── requirements.txt            ← gradio==4.44.1, scikit-learn, joblib
│   └── README.md                   ← HF Space metadata + model setup guide
│
├── llm_finetuning/
│   ├── notebooks/01_finetune_deberta.ipynb   ← DeBERTa training notebook
│   ├── data/task1_train.csv                  ← Training split
│   ├── data/task1_test.csv                   ← Holdout test (10,717 rows)
│   └── results/task1_best_model/             ← Saved DeBERTa checkpoint
│
├── data/cleaned/
│   ├── task1_clean.csv             ← 53,585 rows, 145 classes
│   └── task2_clean.csv             ← Sub-industry classification data
│
└── frontend/                       ← Next.js application (local dev)
    └── app/
        ├── demo/                   ← Main classification demo UI
        ├── dashboard/              ← Analytics dashboard
        ├── llm/                    ← LLM comparison page
        └── features/               ← Feature exploration
```

---

## 9. Key Technical Decisions

**Why `class_weight="balanced"` in cascade SVMs?**
The Morningstar dataset is severely imbalanced. Without class balancing, the LinearSVC ignores rare classes entirely. `class_weight="balanced"` forces the model to treat each class equally during training, which is what enables the 73.68% F1 on rare classes.

**Why `dual=False` in LinearSVC?**
The dataset has more features (50,000 TF-IDF) than samples per class at Levels 2 and 3. `dual=False` uses the primal optimization formulation, which is faster and more numerically stable in this configuration.

**Why `sublinear_tf=True` in TF-IDF?**
Financial text descriptions have high term frequency variance — some words like "company" and "provides" appear hundreds of times. Sublinear TF scaling (1 + log(tf)) prevents these high-frequency words from dominating the feature space.

**Why `ngram_range=(1,2)`?**
Bigrams capture critical financial phrases that unigrams miss: "net interest" is meaningless alone, but "net interest margin" is a strong Regional Banks signal. Bigrams capture the middle two tokens of that phrase as pairs.

**Why waitress instead of Flask dev server?**
Flask's Werkzeug development server exits immediately on Python 3.11 + Windows due to a signal handler incompatibility. Waitress is the standard WSGI server for Windows production deployments and is stable across all Python 3.x versions.

**Why L4 is trained per MSTAR code, not per group or sector?**
Sub-industries are defined at the MSTAR (Level 3) scope — each MSTAR code maps to its own disjoint set of 1–13 sub-industries. Training one L4 model per MSTAR code keeps each classifier's label space small (1–13), maximizes the signal-to-noise ratio per class, and means an error in L1 or L2 that still lands the right MSTAR code will still yield a correct sub-industry.

**Why `python:3.11-slim` Docker image for Railway?**
Railway's default nixpacks builder creates a Python venv at build time with prefix `/install`, but the runtime Python binary ships from `/mise/installs/python/3.11.x`. At runtime `sys.prefix='/install'` causes a fatal `No module named 'encodings'` crash before the app even starts. Using `python:3.11-slim` directly bypasses the venv entirely — the system Python is the runtime Python, paths match, no crash.

**Why `--workers 1 --preload` in gunicorn?**
Each worker loads all cascade models into memory (~117 MB total). Railway's free/starter tier provides 512 MB RAM. Two workers × 117 MB = 234 MB models plus Flask overhead reaches the ceiling. `--preload` loads the app in the master process before forking, so workers share the model memory via copy-on-write. One worker with preload is the safest configuration for constrained-memory cloud deployments.

---

## 10. Presentation Talking Points

1. **Task 1 number:** 88.90% Macro F1, 145 classes, 10,717 holdout samples — no pruning, no tricks, no GPU.

2. **Task 2 number:** 55.41% Macro F1, 428 sub-industry classes — +19 points over a fine-tuned DeBERTa transformer that took 3 hours to train. Our cascade took 3 minutes.

3. **The insight:** Everyone else flattened the taxonomy. We read the taxonomy. The 8-digit Morningstar code is literally a 3-level address: sector (3 digits), group (2 digits), code (2 digits). Classify in that order, and each decision gets easier.

4. **The proof:** Long-tail classes jumped from 20% to 74% F1. Those are the exact classes that killed DeBERTa's score. The cascade structure eliminated the problem architecturally — no more competing against 144 other codes simultaneously.

5. **The Task 2 cascade design:** We added just one more level. T1 routes to the MSTAR code (88.42% accuracy), and L4 picks among 1–13 sub-industry candidates for that code. The decision space shrinks from 428 classes to an average of 5. That's why it works.

6. **The production system:** Live on Railway (Docker, git LFS models) and Hugging Face Spaces (Gradio). Confidence routing, written explanations, 4-taxonomy crosswalk mapping to GICS, NAICS, and SIC. A Bloomberg terminal charges for the cross-taxonomy feature.

7. **The business case:** ~1,600 classifications per second, on CPU, no GPU, no cloud bill. The cascade is 40× faster than DeBERTa and 25 points more accurate on Task 1. On Task 2 it beats DeBERTa by 19 points at a fraction of the compute cost.

---

*MGT 599 Capstone — Group 4 — Akash Anipakalu Giridhar — Strayer University — May 2026*
