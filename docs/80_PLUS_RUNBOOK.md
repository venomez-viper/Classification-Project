# 80+ Macro F1 Runbook

This is the current no-leakage path for the Task 1 breakthrough push.

## Goal

Push the honest `task1_train.csv -> task1_test.csv` Macro F1 above `80%` without using any leaked rows or post-hoc metric inflation.

## Current Position

- Historical leaked result: `88.90%` — not valid.
- Best honest classical family result in repo docs: about `69%`.
- New ambiguity-aware quick classical run: about `61.55%`.

Conclusion: the 80+ path is now a **transformer-on-cleaner-supervision** problem, not a “one more SVM” problem.

## Data To Use

Generate the segment-aware export:

```powershell
python -B scripts\export_task1_segment_aware_for_colab.py
```

This writes:

- `llm_finetuning/data/segment_aware_task1/task1_segment_aware_train.csv`
- `llm_finetuning/data/segment_aware_task1/task1_segment_aware_test.csv`
- `llm_finetuning/data/segment_aware_task1/task1_segment_aware_label_maps.json`

Key fields:

- `text_primary`: segment-only input
- `text_aux`: company-level text
- `text_joint`: segment text + company text
- `label_idx`: industry target
- `sector_idx`: sector target
- `group_idx`: group target
- `sample_weight`: ambiguity-aware training weight

## Highest-Upside Runs

### Run A — ModernBERT on `text_primary`

Purpose: test whether pure segment-only input removes enough contamination to raise the ceiling.

```bash
python llm_finetuning/scripts/train_segment_aware_multitask.py \
  --model-name answerdotai/ModernBERT-base \
  --train-csv /content/task1_segment_aware_train.csv \
  --test-csv /content/task1_segment_aware_test.csv \
  --text-col text_primary \
  --output-dir /content/run_modernbert_primary \
  --max-len 512 \
  --batch-size 8 \
  --eval-batch-size 16 \
  --grad-accum 4 \
  --epochs 6 \
  --lr 2e-5 \
  --bf16 \
  --gradient-checkpointing
```

### Run B — ModernBERT on `text_joint`

Purpose: keep company context, but in a cleaner supervised setup.

```bash
python llm_finetuning/scripts/train_segment_aware_multitask.py \
  --model-name answerdotai/ModernBERT-base \
  --train-csv /content/task1_segment_aware_train.csv \
  --test-csv /content/task1_segment_aware_test.csv \
  --text-col text_joint \
  --output-dir /content/run_modernbert_joint \
  --max-len 512 \
  --batch-size 8 \
  --eval-batch-size 16 \
  --grad-accum 4 \
  --epochs 6 \
  --lr 2e-5 \
  --bf16 \
  --gradient-checkpointing
```

### Run C — DeBERTa-v3-base on `text_primary`

Purpose: compare backbone behavior against ModernBERT.

```bash
python llm_finetuning/scripts/train_segment_aware_multitask.py \
  --model-name microsoft/deberta-v3-base \
  --train-csv /content/task1_segment_aware_train.csv \
  --test-csv /content/task1_segment_aware_test.csv \
  --text-col text_primary \
  --output-dir /content/run_deberta_primary \
  --max-len 384 \
  --batch-size 8 \
  --eval-batch-size 16 \
  --grad-accum 4 \
  --epochs 6 \
  --lr 2e-5 \
  --bf16 \
  --gradient-checkpointing
```

## Decision Gates

- If `text_primary` is not clearly better than the historical mixed-input stack, the contamination hypothesis is weaker than expected.
- If `text_primary` beats `text_joint`, keep company text out of the primary prediction path.
- If a run crosses `75%+`, expand around that exact recipe before trying new architectures.
- If no run gets close to `75%`, revisit the split and the supervision target before burning more compute.

## Promotion Rule

Only promote a model into the web app when all of these are true:

1. Official test Macro F1 is recorded.
2. Artifact reloads cleanly.
3. `training_summary.json` exists.
4. Public-facing metric claim is updated consistently.

## Product Integration

The Flask backend can already prefer the new Task 1 artifact automatically if the segment-aware packaged model exists:

- `server_legendary.py`
- `scripts/segment_aware_predict.py`

That means once a stronger text model is packaged behind the same response contract, the web app can consume it without a frontend rewrite.
