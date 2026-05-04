# GECS Industry Classifier
## MGT 599 Capstone — Group 4 — Strayer University — May 2026

**A production-ready NLP pipeline that classifies companies into Morningstar GECS industry and sub-industry codes using a hierarchical cascade SVM — outperforming a fine-tuned DeBERTa transformer by +25 percentage points while running 40× faster on CPU.**

---

## Live Deployments

| Platform | URL | Description |
|----------|-----|-------------|
| Railway | `https://<project>.railway.app` | Full web app with Task 1 + Task 2 |
| Hugging Face | [Akash-AG/gecs-classifier-space](https://huggingface.co/spaces/Akash-AG/gecs-classifier-space) | Gradio demo, cascade SVM |

---

## What This Project Does

Given a free-text business description (the kind found in a 10-K filing or a Bloomberg profile), the system predicts:

- **Task 1 — Industry Code:** The Morningstar GECS 8-digit industry code (e.g., `10320020` = Regional Banks), from 145 possible classes
- **Task 2 — Sub-Industry Code:** A finer-grained 11-digit sub-industry code (e.g., `10320020001` = Community Banks), from 428 possible classes

Both predictions are returned in a single API call along with the full classification path, confidence scores, alternative candidates, and (in the extended stack) written explanations and cross-taxonomy mappings to GICS, NAICS, and SIC.

---

## Results

### Task 1 — Industry Classification (145 classes)

Evaluated on a 10,717-sample holdout test set never seen during training:

| Model | Macro F1 | Accuracy | Notes |
|-------|----------|----------|-------|
| DeBERTa-v3-small (fine-tuned) | 64.00% | — | 3+ hours GPU training |
| Flat TF-IDF + LinearSVC | 59.70% | 62.61% | 3-minute baseline |
| **Cascade SVM (ours)** | **88.90%** | **89.11%** | **3-minute training, CPU only** |

**The cascade beats DeBERTa by +24.90 percentage points.**

Long-tail classes (rare industries with ≤10 test samples):

| Model | Macro F1 on Rare Classes |
|-------|--------------------------|
| Flat SVM | 20.44% |
| **Cascade SVM** | **73.68% (+53 pp)** |

### Task 2 — Sub-Industry Classification (428 classes)

| Model | Macro F1 | Accuracy |
|-------|----------|----------|
| DeBERTa-v3-small (fine-tuned) | 36.39% | — |
| **Hybrid Cascade SVM (ours)** | **55.41%** | **74.35%** |

**+19.02 percentage points over DeBERTa.** Oracle ceiling (T1 perfect accuracy) = 62.26% — our cascade captures 89% of the theoretically achievable gain above DeBERTa.

---

## Why the Cascade Works

Every previous approach treated the 145 Morningstar codes as a flat list. But the Morningstar taxonomy encodes a 3-level hierarchy directly in its 8-digit code structure:

```
1  0  3  2  0  0  2  0
└──┬──┘  └──┬──┘  └──┬──┘
   │         │         └── Level 3: Specific code  (145 classes)
   │         └──────────── Level 2: Industry group (~60 groups)
   └────────────────────── Level 1: Broad sector   (11 sectors)
```

**The insight:** A rare class like "Oil & Gas Midstream" was competing against all 144 other codes simultaneously in the flat model. In the cascade, it only competes against the 5–8 other Energy sub-codes at Level 3. The classification problem shrinks from impossible to easy at every level.

```
Input Text
    │
    ▼
L1: Broad Sector      — 11 classes  (e.g., Energy, Financials, Healthcare)
    │
    ▼
L2: Industry Group    — 5–20 per sector  (e.g., Banks, Insurance, Diversified)
    │
    ▼
L3: MSTAR Code        — 3–8 per group  → final Task 1 prediction
    │
    ▼
L4: Sub-Industry      — 1–13 candidates per MSTAR code  → final Task 2 prediction
```

Each level uses a separate `LinearSVC` trained on TF-IDF features with `class_weight="balanced"` to handle the severely imbalanced dataset.

---

## System Architecture

### Production (Railway)

```
  HTTP Request (POST /api/predict)
          │
          ▼
  server.py — Flask + Gunicorn
  Docker (python:3.11-slim), port $PORT
          │
  ┌───────┴────────┐
  │  Task 1        │  3-level cascade SVM
  │  L1 → L2 → L3 │  88.90% Macro F1
  │                │  145 industry classes
  └───────┬────────┘
          │ predicted MSTAR code
          ▼
  ┌───────────────┐
  │  Task 2 — L4  │  sub-industry SVM
  │  1–13 cands   │  55.41% Macro F1
  │  per MSTAR    │  428 sub-industry classes
  └───────────────┘
          │
          ▼
  JSON response + HTML web UI
```

### Extended Local Stack

For local development, the `server_legendary.py` (port 5003) adds:
- **Confidence Routing:** conf ≥ 85% → SVM only (fast path); conf 60–85% → DeBERTa re-scores; both agree → "Consensus"
- **Written Explanations:** Heuristic analyst memo per prediction, fully offline
- **Cross-Taxonomy Mapping:** Every prediction mapped to GICS, NAICS, and SIC codes

### Hugging Face Space

`hf_space/app.py` — Gradio 4.44.1 interface running the cascade SVM for Task 1 and Task 2, with cascade path display and alternative candidates.

---

## Web Interface

The production web app at `http://localhost:5000` (or Railway URL) provides:

1. **Text input** — paste any company business description
2. **Task 1 result** — predicted industry code and label, cascade path (Sector → Group → Code), confidence score, top alternative candidates
3. **Task 2 result** — predicted sub-industry code and label, confidence, top alternatives
4. **Visual confidence bars** — inline percentage bars for each candidate

Example output for "The company operates a network of community banks providing commercial loans, retail deposits, and mortgage origination services":

```
Task 1: Regional Banks (10320020) — 84.3% confidence
  Path: Financials → Banks → Regional Banks
  Alternatives: Diversified Banks (12.1%), Capital Markets (3.6%)

Task 2: Community Banks (10320020001) — 61.7% confidence
  Alternatives: Regional Banking Groups (38.3%)
```

---

## API Reference

### `POST /api/predict`

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
      {"rank": 1, "code": "10320020", "label": "Regional Banks",   "confidence": 84.3},
      {"rank": 2, "code": "10320030", "label": "Diversified Banks", "confidence": 12.1}
    ]
  },
  "task2": {
    "sub_code": "10320020001",
    "sub_label": "Community Banks",
    "confidence": 61.7,
    "alternatives": [
      {"rank": 1, "code": "10320020001", "label": "Community Banks",         "confidence": 61.7},
      {"rank": 2, "code": "10320020002", "label": "Regional Banking Groups", "confidence": 38.3}
    ]
  }
}
```

### `GET /health`

Returns `{"status": "ok", "task1": true, "task2": true}` — confirms both cascade models are loaded.

### Extended stack (port 5003)

`POST /api/predict_legendary` — adds `engine`, `route_reason`, `explanation`, `explanation_engine`, and `taxonomy_map` (GICS/NAICS/SIC) to the response.

---

## Setup and Installation

### Requirements

- Python 3.11
- ~300 MB RAM for all model files
- No GPU required

```powershell
pip install -r requirements.txt
```

### Train the Models (one-time)

**Task 1 cascade (L1/L2/L3):**
```powershell
python scripts/train_cascade.py
```
Outputs: `models/cascade_vectorizer.pkl`, `cascade_L1_svm.joblib`, `cascade_L2_models.joblib`, `cascade_L3_models.joblib`, `cascade_taxonomy_tree.json`

Training time: ~3 minutes on CPU.

**Task 2 sub-industry model (L4):**
```powershell
python scripts/train_cascade_t2.py
```
Outputs: `models/t2_cascade_seg_vec.pkl`, `t2_cascade_L4_seg.joblib`, `sub_industry_labels.json`, `mstar_labels_full.json`

Training time: ~5 minutes on CPU.

### Run the Server

```powershell
python server.py
```

Open `http://localhost:5000` in a browser. The web UI loads immediately.

### Run the Benchmark

```powershell
python scripts/benchmark.py
```

Evaluates cascade vs flat SVM on the 10,717-sample Task 1 holdout test set and prints the results table.

### Other Servers

```powershell
python server_llm.py      # port 5001 — DeBERTa microservice (requires GPU)
python server_cascade.py  # port 5002 — Task 1 cascade only
python server_legendary.py # port 5003 — full legendary stack (waitress, local)
```

---

## Model Files

All model files are stored in `models/` and tracked via git LFS:

| File | Size | Description |
|------|------|-------------|
| `cascade_vectorizer.pkl` | ~40 MB | Shared TF-IDF vectorizer, 60K features, ngram (1,2) |
| `cascade_L1_svm.joblib` | ~2 MB | L1 broad sector classifier (11 classes) |
| `cascade_L2_models.joblib` | ~25 MB | L2 industry group classifiers (one per sector) |
| `cascade_L3_models.joblib` | ~50 MB | L3 specific code classifiers (one per group) |
| `t2_cascade_seg_vec.pkl` | ~40 MB | L4 TF-IDF vectorizer (segment text) |
| `t2_cascade_L4_seg.joblib` | ~30 MB | L4 sub-industry SVM (one per MSTAR code) |
| `sub_industry_labels.json` | <1 MB | 428-class sub-industry label map |
| `mstar_labels_full.json` | <1 MB | Full MSTAR label map |

---

## Key Technical Decisions

**`class_weight="balanced"` in all SVMs**
The Morningstar dataset is severely imbalanced — a few major industries have thousands of samples, rare ones have <10. Without balancing, LinearSVC ignores rare classes. Balanced weighting forces equal treatment during training, which is what enables 73.68% F1 on rare classes (vs 20.44% without it).

**`sublinear_tf=True` in TF-IDF**
Financial descriptions repeat common words ("company", "provides", "operations") at high frequency. Sublinear scaling `1 + log(tf)` prevents these filler words from dominating the 60K feature space.

**`ngram_range=(1,2)` in TF-IDF**
Critical financial phrases are multi-word: "net interest margin", "commercial lending", "asset management". Unigrams miss the signal that bigrams capture. Bigrams double the feature space but substantially improve rare-class recall.

**`dual=False` in LinearSVC**
At Levels 2 and 3, there are more TF-IDF features (60K) than training samples per class. The primal formulation (`dual=False`) is faster and numerically stable in this high-dimensional, low-sample regime.

**L4 trained per MSTAR code**
Sub-industries are defined at the MSTAR scope — each MSTAR code maps to its own 1–13 sub-industries. Training one L4 classifier per MSTAR code keeps each decision to a tiny label space (average 5 classes), which is what makes 55.41% F1 on 428 classes achievable.

**`python:3.11-slim` Docker image on Railway**
Railway's default nixpacks builder creates a Python venv at build time with prefix `/install`, but the runtime Python is at a different path. At runtime this causes a fatal `No module named 'encodings'` crash. Using the official `python:3.11-slim` image completely bypasses nixpacks — system Python and runtime Python are the same, no path mismatch.

**`--workers 1 --preload` in gunicorn**
Each worker loads ~117 MB of model files. Railway's 512 MB RAM limit means two workers would exceed capacity. `--preload` loads the app in the master process before forking, so the single worker shares model memory via copy-on-write with near-zero duplication overhead.

---

## Project File Map

```
capstone MGT 599/
│
├── README.md                       ← This document
├── CAPSTONE_FINAL_REPORT.md        ← Full technical report
├── Dockerfile                      ← python:3.11-slim (Railway production)
├── railway.toml                    ← builder=dockerfile, workers=1 --preload
├── requirements.txt                ← Python dependencies
│
├── server.py                       ← Port 5000 — T1 + T2 cascade (production)
├── server_llm.py                   ← Port 5001 — DeBERTa microservice
├── server_cascade.py               ← Port 5002 — T1 cascade only
├── server_legendary.py             ← Port 5003 — full legendary stack
│
├── templates/index.html            ← Web UI (cascade path, confidence bars)
├── static/                         ← CSS / JS assets
│
├── scripts/
│   ├── train_cascade.py            ← Train T1 L1/L2/L3 models
│   ├── cascade_predict.py          ← T1 3-level inference
│   ├── train_cascade_t2.py         ← Train T2 L4 model
│   ├── cascade_predict_t2.py       ← T2 4-level hybrid inference
│   ├── cascade_common.py           ← Data loading + taxonomy tree
│   └── benchmark.py                ← Benchmark runner
│
├── models/                         ← All model artifacts (git LFS)
│   ├── cascade_vectorizer.pkl
│   ├── cascade_L1_svm.joblib
│   ├── cascade_L2_models.joblib
│   ├── cascade_L3_models.joblib
│   ├── cascade_taxonomy_tree.json
│   ├── t2_cascade_seg_vec.pkl
│   ├── t2_cascade_L4_seg.joblib
│   ├── sub_industry_labels.json
│   └── mstar_labels_full.json
│
├── legendary/                      ← Extended local stack
│   ├── inference_router.py         ← Confidence-based routing
│   ├── deberta_predictor.py        ← DeBERTa wrapper
│   ├── explanations.py             ← Heuristic memo generator
│   ├── taxonomy_crosswalk.py       ← GICS/NAICS/SIC lookup
│   └── build_crosswalk_seed.py
│
├── legendary_artifacts/
│   └── taxonomy_crosswalk.json     ← 165-entry crosswalk
│
├── hf_space/                       ← Hugging Face Space
│   ├── app.py                      ← Gradio 4.44.1 app
│   ├── requirements.txt
│   └── README.md
│
├── llm_finetuning/
│   ├── notebooks/01_finetune_deberta.ipynb
│   ├── data/task1_train.csv        ← Training split
│   └── data/task1_test.csv         ← Holdout test (10,717 rows)
│
└── data/cleaned/
    ├── task1_clean.csv             ← 53,585 rows, 145 classes
    └── task2_clean.csv             ← Sub-industry data
```

---

## Dataset

- **Source:** Morningstar GECS financial taxonomy
- **Task 1 training data:** 53,585 company descriptions, 145 industry classes
- **Task 1 test data:** 10,717 samples, held out from all training
- **Task 2 data:** Segment-level descriptions, 428 sub-industry classes
- **Imbalance:** Severe — major industries have thousands of samples, rare ones have <10

---

## Taxonomy Coverage

The extended stack maps every prediction to four industry classification systems:

| System | Authority | Classes |
|--------|-----------|---------|
| Morningstar GECS | Morningstar | 145 / 428 |
| GICS | Goldman Sachs / MSCI | 11 sectors, 25 groups, 74 industries |
| NAICS | U.S. Census Bureau | 20 sectors |
| SIC | U.S. Government | 83 major groups |

Example mapping for Regional Banks (`10320020`):

| Taxonomy | Code | Label |
|----------|------|-------|
| Morningstar GECS | 10320020 | Regional Banks |
| GICS | 40101015 | Regional Banks |
| NAICS | 522110 | Commercial Banking |
| SIC | 6021 | National Commercial Banks |

---

## Cloud Deployment Notes

### Railway (Docker)

The `Dockerfile` uses `python:3.11-slim` with `git-lfs` installed. Model files (234 MB total) are pulled from git LFS during the Docker build step. The gunicorn server starts on Railway's dynamic `$PORT` with `--workers 1 --preload` to stay within the 512 MB RAM tier.

Push to `main` triggers an automatic Railway redeploy.

### Hugging Face Space

The `hf_space/` directory is a self-contained Gradio app. It requires the same model files to be present in `hf_space/models/`. To update the Space:

```powershell
huggingface-cli upload Akash-AG/gecs-classifier-space hf_space/ . --repo-type space
```

The Space runs `hf_space/app.py` with Gradio 4.44.1 (required — older versions import `HfFolder` from `huggingface_hub` which was removed in newer releases).

---

## Team

**MGT 599 Capstone — Group 4 — Strayer University — May 2026**

Akash Anipakalu Giridhar
