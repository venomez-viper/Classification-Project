# TAVSS: Industry Classification System

**MGT 599 Capstone · Group 4 · DePaul University**

TAVSS classifies company and segment descriptions into Morningstar Global Equity Classification Structure (GECS) industry codes. Given a plain-English company description, the system predicts a Task 1 industry code (145 classes) and a constrained Task 2 sub-industry code (428 classes), with confidence scores and alternatives at every level.

---

## Results

| Metric | Score |
|---|---|
| Task 1: Macro F1 (145 classes) | 75.0% |
| Task 1: Top-3 Accuracy | 91.4% |
| Task 2: Macro F1 (428 classes) | 55.44% |
| Evaluation | Company-disjoint test set (10,717 rows) |

The system was built on a company-disjoint train/test split. An earlier result of 88.90% was traced to train/test leakage (97.2% of test rows were memorized during training) and is documented as an audit finding in `CASCADE_AUDIT.md`. The 75.0% figure is the honest, reproducible baseline.

---

## Architecture

```
Company / segment description
          |
          v
ModernBERT-large (multi-task: sector + group + industry heads)
          |
          v
Task 1: 145-class GECS industry code
          |
          v
Task 1 -> Task 2 constraint map
          |
          v
Task 2: 428-class SVM cascade (constrained by Task 1 parent)
          |
          v
Structured JSON response
```

The Task 1 model is a fine-tuned ModernBERT-large with three output heads (sector, group, industry) trained jointly. At inference, log-softmax scores from all three heads are combined with a weighted sum before the final argmax, which provides hierarchical consistency without a hard cascade.

Task 2 uses a constrained SVM cascade. Each Task 1 code has a dedicated L4 classifier trained only on its known sub-industry children. The Task 1 prediction gates which L4 model is invoked.

---

## Deployment

| Layer | Platform |
|---|---|
| Model inference | Hugging Face Space (`akash-ag-gecs-modernbert`) |
| Frontend | Vercel |
| API proxy | Next.js API routes (`/api/predict`) |

The Vercel frontend proxies all classification requests to the Hugging Face Space. The Space runs FastAPI with a Gradio UI and a REST endpoint at `POST /api/predict`.

---

## Repository Structure

```
.
├── hf_space_modernbert/       # HuggingFace Space: FastAPI + Gradio + ModernBERT inference
│   ├── app.py                 # FastAPI app: /api/predict, /health, Gradio UI
│   ├── models/                # best_model_state.pt, industry_classes.npy, label maps
│   └── requirements.txt
│
├── frontend/                  # Next.js app deployed on Vercel
│   ├── app/api/predict/       # Vercel proxy to HF Space
│   ├── components/LiveDemo.tsx
│   └── vercel.json
│
├── colab/                     # Training notebooks (Colab Pro+)
│   └── modernbert_finetune.ipynb
│
├── data/
│   └── cleaned/task1_clean.csv   # Source of truth: 53,585 rows x 10 cols
│
├── llm_finetuning/data/
│   ├── task1_train_with_companyid.csv
│   └── task1_test_with_companyid.csv
│
├── scripts/
│   ├── train_cascade_t2.py    # Builds Task 2 constrained cascade
│   └── cascade_predict_t2.py  # Hybrid Task 1 + Task 2 inference
│
├── models_task2/              # Task 2 SVM artifacts
├── gecs_taxonomy.json         # Parsed GECS taxonomy definitions
├── server_legendary.py        # Local Flask server (port 5003)
├── CASCADE_AUDIT.md           # Leakage audit and methodology record
└── RESULTS.md                 # Experiment leaderboard
```

---

## Local Development

**Requirements:** Python 3.11, Node.js 18+

Install dependencies:

```powershell
pip install -r requirements.txt
cd frontend && npm install --legacy-peer-deps
```

Run the local API server:

```powershell
python server_legendary.py
```

Run the frontend (points to `http://localhost:5003` by default):

```powershell
cd frontend
npm run dev
```

Override the API target with the `GECS_API_URL` environment variable to point at the HuggingFace Space instead:

```powershell
$env:GECS_API_URL = "https://akash-ag-gecs-modernbert.hf.space"
cd frontend && npm run dev
```

---

## API

The HuggingFace Space exposes a REST endpoint:

```
POST https://akash-ag-gecs-modernbert.hf.space/api/predict
Content-Type: application/json

{ "text": "The company operates a network of community banks..." }
```

Response:

```json
{
  "success": true,
  "engine": "ModernBERT-large",
  "model_version": "tavss-modernbert-v3",
  "mstar_code": "10320020",
  "mstar_label": "Banks - Regional",
  "confidence_t1": 84.2,
  "alternatives_t1": [
    { "rank": 1, "code": "10320020", "label": "Banks - Regional", "confidence": 84.2 },
    { "rank": 2, "code": "10320010", "label": "Banks - Diversified", "confidence": 9.1 },
    { "rank": 3, "code": "10321010", "label": "Savings & Cooperative Banks", "confidence": 3.4 }
  ],
  "task2": {
    "code": "1032002002",
    "subindustry_name": "Corporate banking",
    "confidence_percent": 61.3,
    "alternatives": []
  },
  "latency_ms": 4821.3
}
```

Health check:

```
GET https://akash-ag-gecs-modernbert.hf.space/health
```

---

## Training

The Task 1 model was trained in Google Colab Pro+ using `colab/modernbert_finetune.ipynb`. Training inputs are `task1_train_with_companyid.csv` and `gecs_taxonomy.json`. The notebook outputs a zip bundle containing `best_model_state.pt` and `industry_classes.npy`.

Key training details:

- Base model: `answerdotai/ModernBERT-large` (hidden size 1024)
- Three output heads: sector (11 classes), group (55 classes), industry (145 classes)
- Loss: joint cross-entropy across all three heads
- Inference scoring: `log_softmax(industry) + 0.30 * log_softmax(group)[sector_idx] + 0.03 * log_softmax(sector)[sector_idx]`
- Evaluation: company-disjoint split, no company appears in both train and test

Task 2 cascade:

```powershell
python scripts/train_cascade_t2.py
```

---

## Data

The source of truth is `data/cleaned/task1_clean.csv` (53,585 rows). Columns: `CompanyId`, `LongProfile`, `SegmentName`, `SegmentDescription`, `Revenue`, `total_revenue_company_as_of`, `revenue_share`, `is_largest_share_segment`, `MstarGlobal`.

The dataset contains multi-segment companies: 35.1% of companies map to more than one industry code, which creates inherent label ambiguity at the row level. This is the primary ceiling driver for Macro F1 on the row-level test set.

---

## Audit

The original V3 cascade reported **88.90% Macro F1**. A post-hoc audit found that 97.2% of test rows had identical company profiles in the training set (leakage via `task1_clean.csv` used as both train source and test source without a company-disjoint split).

After rebuilding with a proper company-disjoint split:

| Approach | Honest Macro F1 |
|---|---|
| TF-IDF cascade (baseline) | 59.65% |
| V8 mega-ensemble (TF-IDF + sentence embeddings) | 68.42% |
| ModernBERT-large v2 | 67.18% |
| ModernBERT-large v3 (calibrated ensemble) | **75.0%** |

Full audit record: [`CASCADE_AUDIT.md`](CASCADE_AUDIT.md)

---

## Team

Group 4 · MGT 599 Capstone · DePaul University
