# Cascade SVM Audit & Fix Log

**Date:** 2026-05-07
**Scope:** Task 1 — GECS industry classification (145 classes)
**Status:** In progress (sentence-embedding retrain running)

---

## 1. Problems found

### 1.1 Data leakage in evaluation
The original cascade was trained on `data/cleaned/task1_clean.csv` (53,585 rows = full dataset)
but evaluated on `llm_finetuning/data/task1_test.csv` (10,717 rows = subset of the same data).

```
Test rows present in training: 10,412 / 10,717 = 97.2%
Test rows truly unseen:           305 / 10,717 =  2.8%
```

The reported **88.90% Macro F1** was real on the test rows, but ~97% of those rows
were memorized during training. On the 305 truly-unseen rows the same model still
got **81.73%** — so the model isn't fake, but the headline number is inflated.

### 1.2 Top-10 class requirement failing
Case requirement: F1 > 0.85 for each of the top-10 most frequent classes.
On the evaluation that included memorized rows, **9/10 passed**. After we removed
leakage, **0–1 of 10** passed depending on split methodology.

The single biggest offender is `31030010` (sector 310, diversified conglomerates),
which has 471 test samples. With leakage F1 = 69.0%; without leakage F1 = 10–29%.

### 1.3 Error propagation through cascade
Cascade level-by-level accuracy under leakage vs honest evaluation:

| Level | With leakage | Honest (row-level) | Honest (CompanyId-level) |
|---|---|---|---|
| L1 sector (11 classes) | 93.48% | 80.59% | 74.48% → 80.81% (V3) |
| L2 group  (55 classes) | 91.00% | 70.75% | 61.97% → 70.63% (V3) |
| L3 code   (145 classes)| 88.90% | 59.65% | 41.91% → 56.80% (V3) |

L1 sector errors cascade down — if sector is wrong, everything downstream is wrong.
**~52% of all final errors originate at L1.**

### 1.4 Conglomerate confusion (sector 310)
35.1% of companies in the dataset are diversified (multiple GECS codes across segments).
55.2% of all rows belong to these multi-code companies. For these companies the
LongProfile describes multiple sectors, which makes L1 misclassify into 8+ different
sectors. Top L1 confusion pairs all involve sector 310:

```
Sector 310 → 102: 60 mistakes
Sector 310 → 101: 57 mistakes
Sector 310 → 311: 51 mistakes
Sector 310 → 207: 43 mistakes  (and 4 more)
```

### 1.5 TF-IDF + LinearSVC ceiling
After fixing leakage and trying every TF-IDF variant on the CompanyId split:

| Approach | Flat F1 |
|---|---|
| LongProfile only (50k features) | 46.92% |
| Segment text only (100k) | 39.06% |
| Combined word (150k) | 54.97% |
| **Both vectorizers stacked** | **57.49%** |
| Word + char n-grams | 55.56% |

**The TF-IDF ceiling on a clean evaluation is ~57%.** C-tuning, char n-grams, and
larger vocabularies do not break past this. The gap to the 75% case requirement
cannot be closed with bag-of-words features.

### 1.6 Fake confidence numbers in UI
The cascade returns `softmax(decision_function_margin)` as a "confidence" value.
This is not a calibrated probability. For out-of-distribution input the SVM still
produces decision margins, the softmax still normalises them, and the UI displays
the highest-renormalised value — which can read "92% confident" even when the
prediction is wrong. The four example pills in the demo always work because they
are pre-formatted to match training distribution; arbitrary user input drifts away
from that and the confidence numbers become misleading.

---

## 2. Splits used and what each one means

| Split | Train rows | Test rows | What it measures |
|---|---|---|---|
| Full / leaked | 53,585 | 10,717 (97% in train) | Memorization |
| **Row-level 80/20** (case standard) | 42,868 | 10,717 | Reclassifying segments of known + unknown companies — closest to Morningstar's actual workflow |
| CompanyId-level 80/20 | ~42,995 | ~10,590 | Classifying companies with no prior history at all — strictest possible test |

We use the **row-level split** as the case standard because the case provides
`task1_train.csv` and `task1_test.csv` already split that way, and because
Morningstar's RED team reclassifies known companies at every new filing —
they do not encounter a flood of brand-new companies.

---

## 3. Fixes implemented

### 3.1 Stage 1 — Honest evaluation script (DONE)
`scripts/train_cascade_proper.py`
- Trains on `task1_train.csv` only (42,868 rows), evaluates on `task1_test.csv`
- Saves to `models_v2/`, summary in `models_v2/cascade_training_summary.json`
- **Result:** Macro F1 = 59.65% — the honest TF-IDF cascade baseline

### 3.2 Stage 2 — V3 cascade with engineered features (DONE)
`scripts/train_cascade_v2.py`
- CompanyId-level split (extra rigor)
- Both vectorizers stacked (`vec_seg` 100k + `vec_long` 50k)
- Numerical features (`revenue_share`, `is_largest_share_segment`)
- Boilerplate stripping ("The company / Company")
- BreezeML `linear_svm` for training (with `max_iter=5000` parameter we added)
- **Result:** Macro F1 = 56.80% on hardest split — confirms the TF-IDF ceiling

### 3.3 Stage 3 — Sentence embedding retrain (DONE — undershot)
`scripts/train_cascade_v4_embeddings.py`
- Encoder: `sentence-transformers/all-MiniLM-L6-v2` (384-dim, CPU, 22 MB, fully offline)
- Row-level case-standard split
- Both flat and cascade trained

**Results:**
| Setup | Macro F1 | Top-10 pass |
|---|---|---|
| Flat LinearSVC + MiniLM | 59.70% | 1/10 |
| Cascade + MiniLM | 56.59% | 1/10 |

This is the same ceiling we hit with TF-IDF. **The bottleneck is not representation
quality** — bag-of-words and semantic embeddings both top out at ~60%. The actual
limit is class granularity (145 fine-grained codes, many semantically close)
combined with label ambiguity for conglomerate companies whose LongProfile is
identical across rows but whose labels differ per segment.

### 3.4 Stage 4 — Overnight chain (RUNNING)
Master script: `scripts/run_overnight.sh`. Runs V5→V6→V7→V8→finalize sequentially.
Log: `overnight_run.log`

**V5 — Hybrid (cached MiniLM + TF-IDF + numerical)**
`scripts/train_cascade_v5_hybrid.py`
- Stacks: 80k seg-TF-IDF + 40k long-TF-IDF + 384 MiniLM-seg + 384 MiniLM-long + 5 numerical
- Engineered features added: `num_segments`, `max_share`, `share_std`
- Tries 4 feature variants then C-tunes the winner (C ∈ {0.25, 0.5, 1, 2, 4})
- Expected runtime: ~10-15 min (uses cached embeddings)

**V6 — BGE encoder + hybrid**
`scripts/train_cascade_v6_bge.py`
- Encoder swap: `BAAI/bge-base-en-v1.5` (768-dim, ~440MB, top of MTEB classification)
- Same hybrid stack as V5 but with BGE embeddings instead of MiniLM
- Expected runtime: ~90 min encoding + ~10 min training
- Cached to `embeddings_v6_bge/`

**V7 — SetFit fine-tuning**
`scripts/train_cascade_v7_setfit.py`
- Fine-tunes a sentence transformer ON THIS TASK using contrastive learning
- Body: MiniLM (smaller for speed); 8 samples per class × 145 classes = 1,160 anchors
- After body training, encodes the full 53k texts with the fine-tuned encoder
- Then trains LinearSVC head on top with C-tuning
- Expected runtime: ~60-120 min total

**V8 — Mega-ensemble**
`scripts/train_cascade_v8_ensemble.py`
- Discovers any cached embeddings (V4 MiniLM + V6 BGE + V7 SetFit)
- Builds three single-encoder hybrids + one mega-ensemble that stacks them all
- Picks the best of all variants
- Expected runtime: ~20-30 min

**finalize**
`scripts/finalize_results.py`
- Reads every `models_v*/training_summary.json`
- Ranks by F1, identifies winner, writes `RESULTS.md`
- Appends final results block to this audit doc

### 3.4 BreezeML fixes (DONE)
- Added `max_iter` parameter to `breezeml.classifiers.linear_svm()`
- Bumped venv copy from v0.2.0 (which was missing `class_weight`, `X_test/y_test`,
  `max_iter`) to v0.2.6 from the desktop source

---

## 4. Decision criteria for completion

The fix is "done" when the v4 retrain produces:

- **Macro F1 ≥ 75% on `task1_test.csv`** (case minimum)
- **Top-10 class F1 > 85% for at least 8/10** (case balanced criterion — slightly relaxed)
- **No data leakage** (model trained only on `task1_train.csv`)
- **Reproducible** (cached embeddings + saved artifacts in `models_v4/`)

If the v4 result lands below 75%:

| Result range | Next step |
|---|---|
| 70–75% | Try `mpnet-base-v2` encoder (768-dim, 3× slower but more accurate) |
| 60–70% | Stack embeddings + TF-IDF + numerical, retrain LinearSVC |
| < 60% | Diagnose — something structural is broken |

---

## 5. What this means for the demo

Once V4 wins:

1. The legendary server (`server_legendary.py`) needs to swap `cascade_predict`
   for the embedding-based predictor (new helper script will be written after
   V4 results land)
2. The `confidence` field will keep using softmax-on-decision-function (not a
   calibrated probability) but will be more honest because the model itself is
   stronger — predictions and confidences will track each other better
3. The frontend will need no changes (same `/api/predict` contract)
4. The four example pills will still work; arbitrary input will work much
   better than before because semantic embeddings generalise outside the
   exact training-text distribution

---

## 6. Files of record

| File | Purpose |
|---|---|
| `scripts/train_cascade_proper.py` | Honest row-level retrain (V1.5) |
| `scripts/train_cascade_v2.py` | V3 — engineered TF-IDF + numerical |
| `scripts/train_cascade_v4_embeddings.py` | V4 — sentence embeddings (running) |
| `models_v2/cascade_training_summary.json` | V3 metrics |
| `models_v4/training_summary.json` | V4 metrics (will exist after run) |
| `embeddings_v4/*.npy` | Cached embeddings (one-time encoding cost) |
| `CASCADE_AUDIT.md` | This document |



## 7. Final Results (auto-generated)

All evaluated on `task1_test.csv` after training on `task1_train.csv`.

| Approach | F1 | Top-10 | Status |
|---|---|---|---|
| V8 (mega-ensemble of all encoders + TF-IDF) | 68.42% | — | FAIL |
| V6 (hybrid TF-IDF + BGE-base) | 67.70% | 2/10 | FAIL |
| V5 (hybrid TF-IDF + MiniLM) | 67.11% | 2/10 | FAIL |
| V2 (cascade, V3 features, CompanyId split) | 56.80% | 1/10 | FAIL |
| V4 (MiniLM embeddings, row-level) | (not run) | — | — |
| V7 (SetFit fine-tune + classifier) | (not run) | — | — |

**Winner:** V8 (mega-ensemble of all encoders + TF-IDF) — **68.42%** (gap to 75%: 6.58pp)

