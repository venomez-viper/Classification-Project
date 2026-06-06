# Week 4 — BreezeML Level 2 Team Guide
## MGT 599 Capstone · Group 4 · DePaul University Chicago

**Reference files for this guide:**
- `docs/model_version_history.md` — full version history from Week 1 onward
- `docs/Week3_Model_Architecture_and_Pipeline.md` — previous pipeline design
- `CAPSTONE_FINAL_REPORT.md` — final benchmark results and architecture reference
- `scripts/train_cascade.py` — Level 2 training script
- `scripts/benchmark.py` — comparison benchmark runner
- `llm_finetuning/scripts/train_local.py` — DeBERTa fine-tuning script

---

## What Changed This Week

Last week we used **breezeml v0.2.5** with a flat LinearSVC — one classifier competing across all 145 Morningstar classes simultaneously. This week we extended that into **BreezeML Level 2**: a 3-level cascade that mirrors the actual Morningstar taxonomy tree.

| Metric | Last Week (Flat SVM) | This Week (Level 2 Cascade) | Change |
|--------|---------------------|------------------------------|--------|
| Task 1 Macro F1 | 59.70% | **88.90%** | +29.2 pp |
| Task 1 Weighted F1 | 86.82% | **88.90%** | +2.1 pp |
| Accuracy | 62.61% | **89.11%** | +26.5 pp |
| Rare-class Macro F1 (≤10 samples) | 20.44% | **73.68%** | +53.2 pp |
| DeBERTa (fine-tuned, for reference) | 64.00% | — | cascade beats it by +24.9 pp |

**Why the gap is so large:** The flat model forced "Oil & Gas Midstream" to compete against all 144 other codes. The cascade makes it compete only against 5–8 other Energy sub-codes. Every rare class benefits from this structural change.

---

## Level 2 Architecture

```
Input text
    │
    ▼  TF-IDF (50,000 features, bigrams, sublinear_tf)
    │
    ▼  L1 — Broad Sector  (11 sectors)       ← single LinearSVC
    │
    ▼  L2 — Industry Group  (5–20 per sector) ← one LinearSVC per sector
    │
    ▼  L3 — Morningstar Code  (3–8 per group) ← one LinearSVC per group
    │
    ▼  Final 8-digit GECS code
```

Morningstar's own code structure tells you how to build the tree:

```
Code: 1  0  3  2  0  0  2  0
       └──┬──┘  └──┬──┘  └──┬──┘
          │         │         └── L3: Specific code
          │         └──────────── L2: Industry group
          └────────────────────── L1: Broad sector
```

The same TF-IDF vectorizer is shared across all three levels. Only the classifiers change.

---

## Step 1 — Set Up Your Environment

All scripts run from the **project root**. Use system Python (not the `.venv`) because that is where Flask, transformers, and waitress are installed.

```powershell
cd "C:\Users\akash\Desktop\capstone MGT 599"
python --version   # should be 3.11.x
python -c "import breezeml; print(breezeml.__version__)"  # should be 0.2.5
```

If breezeml is missing:
```powershell
pip install breezeml==0.2.5
```

---

## Step 2 — Train BreezeML Level 2 (Cascade)

The training script is `scripts/train_cascade.py`. It reads from `data/cleaned/task1_clean.csv` and writes three model files to `models/`.

```powershell
python scripts/train_cascade.py
```

**What gets written to `models/` after training:**

| File | Contents |
|------|----------|
| `cascade_L1_svm.joblib` | Broad sector classifier (11 classes) |
| `cascade_L2_models.joblib` | Dict of industry group classifiers, one per sector |
| `cascade_L3_models.joblib` | Dict of code classifiers, one per group |
| `cascade_vectorizer.pkl` | Shared TF-IDF vectorizer |
| `cascade_taxonomy_tree.json` | Taxonomy tree derived from training data |

Training takes **2–5 minutes on CPU**. You will see output like:

```
Building taxonomy tree...
  Sectors: 11
  Groups:  67
  Codes:   145
Training L1 (sector)...  done
Training L2 (11 sector models)...  done
Training L3 (67 group models)...  done
Saved to models/
```

### Optional arguments

```powershell
# Change vocabulary size (default 50000)
python scripts/train_cascade.py --max-features 30000

# Change training data path
python scripts/train_cascade.py --input data/cleaned/task1_clean.csv
```

---

## Step 3 — Run the Benchmark

The benchmark compares Level 2 against the flat SVM on the same 10,717-sample holdout test set that was never seen during training.

```powershell
python scripts/benchmark.py
```

Expected output:

```
==============================================================
  MGT 599 Capstone  —  Model Benchmark
==============================================================
  10,717 samples  |  145 unique classes

Running Cascade on 10,717 samples...
  Macro F1    :  88.90%
  Weighted F1 :  88.90%
  Accuracy    :  89.11%
  Time : 6.4s  |  1673 samples/sec

Running Flat SVM on 10,717 samples...
  Macro F1    :  59.70%
  Weighted F1 :  61.96%
  Accuracy    :  62.61%

  FINAL SUMMARY
==============================================================
  DeBERTa fine-tuned  (reported)  :  64.00%
  Flat SVM            (measured)  :  59.70%
  Cascade SVM         (measured)  :  88.90%
  Cascade vs Flat SVM             :  +29.20%
  Cascade vs DeBERTa              :  +24.90%
==============================================================
  Long-Tail  (classes with <= 10 test examples)
  Flat SVM F1   on rare :  20.44%
  Cascade  F1   on rare :  73.68%
  Delta                 : +53.24%
```

If your numbers differ, the most likely cause is that the cascade models in `models/` were trained on different data. Retrain with Step 2 and re-run.

---

## Step 4 — Start the Servers and Test Live

### Start BreezeML Level 2 server (port 5003)

```powershell
python server_legendary.py
```

You should see:
```
Legendary server starting on http://localhost:5003
```

### Verify it is running

```powershell
# Health check
Invoke-WebRequest -Uri http://localhost:5003/health | Select-Object -ExpandProperty Content
```

Expected:
```json
{"ok": true, "cascade_ready": true, "crosswalk_entries": 165}
```

### Send a test classification

```powershell
$body = '{"text": "The company provides retail banking, mortgage lending, and investment portfolio management for individual clients."}'
Invoke-WebRequest -Uri http://localhost:5003/api/predict_legendary -Method POST -Body $body -ContentType "application/json" | Select-Object -ExpandProperty Content
```

You should get back a JSON response with:
- `mstar_code` — 8-digit Morningstar code (e.g. `"10320020"`)
- `mstar_label` — human label (e.g. `"Regional Banks"`)
- `confidence` — softmax confidence %
- `engine` — which path was used (`"SVM Cascade"`)
- `explanation` — analyst memo text
- `taxonomy_map` — cross-mapped to GICS, NAICS, SIC

### Start the DeBERTa server (port 5001)

```powershell
python server_llm.py
```

DeBERTa loads the model into VRAM on startup. This takes 15–30 seconds.

```powershell
# Test DeBERTa
$body = '{"text": "The company designs tiny silicon chips used inside smartphones and laptops."}'
Invoke-WebRequest -Uri http://localhost:5001/api/predict_llm -Method POST -Body $body -ContentType "application/json" | Select-Object -ExpandProperty Content
```

### Start the frontend

```powershell
cd "C:\Users\akash\Desktop\capstone MGT 599\frontend"
npm run dev
```

Open `http://localhost:3000/demo` for the BreezeML Level 2 demo.
Open `http://localhost:3000/llm` for the DeBERTa demo.

---

## Step 5 — Fine-tune DeBERTa (Task 2)

Task 1 DeBERTa is already trained and stored in `llm_finetuning/results/task1_best_model/`.

Task 2 (407 subindustry codes) has not been trained yet. Run:

```powershell
python llm_finetuning/scripts/train_local.py --task task2
```

**What this does:**
- Loads `llm_finetuning/data/task2_train.csv` (22,012 rows, 407 classes)
- Fine-tunes DeBERTa-v3-small for 6 epochs with gradient accumulation
- Saves the best checkpoint to `llm_finetuning/results/task2_best_model/`

**Time:** ~3–4 hours on RTX 3050 (batch size 4, grad accumulation 4).

**To resume from a checkpoint if training was interrupted:**

```powershell
python llm_finetuning/scripts/train_local.py --task task2 --resume
```

Once done, restart `server_llm.py`. The LLM demo page will automatically show both Task 1 (industry) and Task 2 (subindustry) results.

---

## Step 6 — Compare Your Results to Last Week

Run the flat SVM server (Week 3 baseline) on port 5000:

```powershell
python server.py   # port 5000
```

Then test the same description against both servers:

```powershell
$text = "The company manufactures surgical robots and minimally invasive instruments for hospitals."

# Week 3 — Flat SVM
$body = "{`"text`": `"$text`"}"
Write-Host "=== WEEK 3 — Flat SVM ==="
Invoke-WebRequest -Uri http://localhost:5000/api/predict -Method POST -Body $body -ContentType "application/json" | Select-Object -ExpandProperty Content

# This week — BreezeML Level 2
Write-Host "=== WEEK 4 — BreezeML Level 2 ==="
Invoke-WebRequest -Uri http://localhost:5003/api/predict_legendary -Method POST -Body $body -ContentType "application/json" | Select-Object -ExpandProperty Content
```

For a systematic comparison across all 10,717 test samples, run:

```powershell
python scripts/benchmark.py
```

---

## File Reference Map

```
capstone MGT 599/
│
├── server.py                 ← Week 3 — flat breezeml SVM (port 5000)
├── server_llm.py             ← DeBERTa microservice (port 5001)
├── server_legendary.py       ← BreezeML Level 2 — full stack (port 5003)
│
├── scripts/
│   ├── cascade_common.py     ← data loading, taxonomy tree builder
│   ├── train_cascade.py      ← train Level 2 cascade (run this)
│   ├── cascade_predict.py    ← inference — called by server_legendary.py
│   └── benchmark.py          ← compare Level 2 vs flat vs DeBERTa
│
├── models/                   ← trained artifacts go here
│   ├── cascade_L1_svm.joblib
│   ├── cascade_L2_models.joblib
│   ├── cascade_L3_models.joblib
│   ├── cascade_vectorizer.pkl
│   ├── task1_svm_model.joblib      ← Week 3 flat SVM (already exists)
│   └── task1_tfidf_vectorizer.pkl  ← Week 3 vectorizer (already exists)
│
├── llm_finetuning/
│   ├── scripts/train_local.py  ← DeBERTa fine-tuning (--task task1 or task2)
│   ├── data/task1_train.csv    ← 42,868 training rows
│   ├── data/task2_train.csv    ← 22,012 training rows
│   └── results/
│       ├── task1_best_model/   ← DeBERTa Task 1 checkpoint (done)
│       └── task2_best_model/   ← DeBERTa Task 2 checkpoint (needs training)
│
├── legendary/
│   ├── shared.py              ← label lookup, normalize_code
│   ├── inference_router.py    ← 3-tier routing logic
│   ├── explanations.py        ← heuristic analyst memo generator
│   └── taxonomy_crosswalk.py  ← GICS / NAICS / SIC mapping
│
├── legendary_artifacts/
│   └── taxonomy_crosswalk.json ← 165-entry crosswalk (all 145 codes)
│
├── data/cleaned/
│   ├── task1_clean.csv         ← 53,585 rows, 145 classes (full dataset)
│   └── task2_clean.csv         ← subindustry dataset
│
└── docs/
    ├── model_version_history.md        ← Week 1→3 version history
    ├── Week3_Model_Architecture_and_Pipeline.md
    └── Week4_BreezeML_Level2_Team_Guide.md  ← this file
```

---

## Quick Troubleshooting

**"No module named breezeml"**
```powershell
pip install breezeml==0.2.5
```

**"cascade_L1_svm.joblib not found"** — models not trained yet:
```powershell
python scripts/train_cascade.py
```

**server_legendary.py exits immediately** — use system Python, not `.venv`:
```powershell
C:\Users\akash\AppData\Local\Programs\Python\Python311\python.exe server_legendary.py
```

**DeBERTa server slow to start** — normal. The model is loading ~180M parameters into VRAM. Wait 20–30 seconds before sending requests.

**Port already in use:**
```powershell
# Find what is on port 5003
netstat -ano | findstr :5003
# Kill it by PID
Stop-Process -Id <PID> -Force
```

---

*MGT 599 Capstone · Group 4 · DePaul University Chicago · Week 4 · May 2026*
