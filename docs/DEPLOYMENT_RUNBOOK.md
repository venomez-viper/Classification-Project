# GECS-Sage Deployment Runbook

This runbook is the practical checklist for demo day and release prep. It follows the current source of truth: V13 is the locked deployable Task 1 baseline unless a newer artifact is reproduced and saved cleanly, Task 2 is the constrained cascade, and the historical 88.90% result is an audit finding only.

## 1. Local Demo Stack

### Start the Flask API

```powershell
python server_legendary.py
```

Expected default URL:

```text
http://localhost:5003
```

Health check:

```powershell
Invoke-RestMethod http://localhost:5003/health
```

Expected signs of readiness:

- `ready` is true.
- Task 1 model assets load.
- Task 2 assets load from `models_task2/`.
- `model_version` is present.

### Smoke-Test Prediction

```powershell
Invoke-RestMethod http://localhost:5003/predict `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"company_text":"The company operates community banks providing commercial lending, deposits, and mortgage origination.","segment_text":"Regional banking and commercial lending","include_reasoning":true}'
```

Expected response fields:

- `prediction_id`
- `model_version`
- `task1.code`
- `task1.industry_name`
- `task2.code`
- `task2.subindustry_name`
- `trace`

## 2. Frontend Demo

```powershell
cd frontend
npm.cmd run dev
```

Default frontend:

```text
http://localhost:3000
```

The proxy defaults to:

```text
GECS_API_URL=http://localhost:5003
```

Override if needed:

```powershell
$env:GECS_API_URL="http://localhost:5003"
npm.cmd run dev
```

Demo pages to verify:

- `/`
- `/about`
- `/demo`
- `/model`

Public wording rule:

- Say `67.99% locked Task 1 baseline`.
- Say `55.44% Task 2 constrained cascade`.
- Say `88.90% leakage audit finding`, never shipped performance.

## 3. Hugging Face Space

Files that matter:

- `hf_space/app.py`
- `hf_space/README.md`
- `hf_space/requirements.txt`
- model artifacts copied into the Space asset directory

Before pushing Space changes:

```powershell
python -m py_compile hf_space/app.py
```

Space card wording must remain audit-safe:

- Task 1: audited cascade baseline over 145 GECS classes.
- Task 2: 55.44% Macro F1 over 428 constrained classes.
- Historical 88.90% result is leakage-contaminated and not the shipped claim.

## 4. Colab Training Outputs

### ModernBERT

Notebook:

```text
colab/modernbert_finetune.ipynb
```

Upload:

- `task1_train.csv`
- `task1_test.csv`
- `gecs_taxonomy.json`

Record after every run:

- best dev Macro F1
- official test Macro F1
- top-10 class pass count
- output zip filename
- whether checkpoint was saved

Promotion rule:

- Do not update public performance claims unless the artifact is saved, reloadable, and evaluated on the official test split.

### Qwen Teacher Labels

Notebook:

```text
colab/distill_step1_teacher_label.ipynb
```

Upload:

- Task 1 training CSV
- `gecs_taxonomy.json`

Output is for reasoning chains and later distillation. It is not the primary classifier.

## 5. Verification Commands

Backend:

```powershell
python -m py_compile hf_space/app.py server_legendary.py scripts/train_cascade_t2.py scripts/cascade_predict_t2.py
```

Targeted frontend lint:

```powershell
cd frontend
npx.cmd eslint app/about/page.tsx app/page.tsx components/Hero.tsx components/HowItWorks.tsx components/ModelDevelopment.tsx components/Evaluation.tsx components/LiveDemo.tsx components/BreezeMLSection.tsx app/api/predict/route.ts app/api/health/route.ts
```

Full frontend lint currently includes older dashboard debt. Do not block the release on unrelated legacy dashboard lint unless those pages are part of the live demo path.

## 6. Release Checklist

- Local Flask `/health` passes.
- Local Flask `/predict` returns Task 1 and Task 2.
- Frontend `/demo` works against `localhost:5003`.
- README and Space card use audit-safe metrics.
- `serve/*.sqlite` remains ignored.
- `models_task2/*.joblib` and `models_task2/*.pkl` are tracked by Git LFS.
- No BusinessBERT files are introduced into `colab/`.
- Any new model claim has a saved artifact and an evaluation log.

## 7. Emergency Demo Fallbacks

If the frontend fails:

- Use `Invoke-RestMethod` against `/predict`.
- Show `README.md`, `CASCADE_AUDIT.md`, and `HANDOFF_PLAYBOOK.md`.

If Flask fails:

- Show the Colab output zip metrics.
- Show the runbook and audit story.
- Do not improvise a higher metric.

If HF Space fails:

- Use localhost.
- State that the deployed product path and local backup share the same model contract.

## 8. One-Sentence Pitch

GECS-Sage is an honest, inspectable Morningstar GECS classifier that turned a leakage discovery into a stronger product: reproducible Task 1 baseline, constrained Task 2 routing, taxonomy grounding, and analyst-ready prediction logs.
