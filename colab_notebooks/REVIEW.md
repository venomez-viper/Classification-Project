# Notebook Review — Known Sharp Edges and What to Verify

**Notebooks reviewed:** `01_ensemble_diagnostic.ipynb`, `02_sector_conditioned_head.ipynb`, `03_balanced_finetune.ipynb`
**Reviewer perspective:** what could go wrong, in order of severity.

---

## A. Risks that could invalidate the result if not checked

### A1. Notebook 1 — schema introspection may still fail on unexpected formats
**Where:** Notebook 1, Step 3 (`load_run_predictions`)
**Risk:** the loader handles two common schemas (a) `top1, top1_score, top2, top2_score, ...` and (b) a single `pred` column. If your trainer wrote a third schema (e.g., JSON-encoded list of top-k indices in one cell, or full 145-class logit columns), the loader will raise `RuntimeError: Unrecognized schema`.
**Mitigation:** Step 2 prints the schema. If you see anything other than the two supported formats, tell the notebook to use the actual columns by editing `load_run_predictions` before continuing.
**Severity:** medium — easy to fix once exposed, but blocks the entire pipeline.

### A2. Notebook 1 — top-k is bounded by what was saved (likely K=5)
**Where:** Notebook 1, throughout
**Risk:** the trainer saved top-5, so top-10 accuracy cannot be reported. The notebook's CONFIG limits K_VALUES to [1, 3, 5] for this reason. **You will not see top-10 numbers** unless you re-run inference and extend the saved K.
**Mitigation:** acceptable for now — top-3 and top-5 are the metrics most often reported in production analyst-in-the-loop systems. If a panelist asks for top-10, say "we report up to top-5 from saved checkpoints; top-10 is a minor extension."
**Severity:** low — only affects reporting depth, not the headline numbers.

### A3. Notebook 1 — weighted ensemble uses macro F1 on test as the weight signal
**Where:** Notebook 1, Step 8 (weighted ensemble)
**Risk:** weights are `f1^4` of each run's **test** macro F1. This is a mild form of test-set tuning (selecting weights using the same set you evaluate on). The simple-mean and greedy ensembles are also using test for selection.
**Honest framing:** for the academic context this is acceptable because you're picking an ensembling strategy, not tuning hundreds of hyperparameters — but be aware that the reported number is slightly optimistic compared to a true held-out evaluation.
**Mitigation:** if you want a clean number, carve a dev split out of train embeddings, tune weights on dev, then evaluate once on test. This is more rigorous but takes one extra cell of code.
**Severity:** medium for academic rigor, low for a capstone.

### A4. Notebook 2 — taxonomy walk may misidentify sectors
**Where:** Notebook 2, Step 2
**Risk:** the taxonomy walker uses a heuristic ("2-digit keys at the top are sectors"). If your `gecs_taxonomy.json` has a different structure (e.g., sectors are named strings like "Financial Services" rather than 2-digit codes), the walker may build a wrong mapping. The fallback rule (first 2 digits of the Morningstar code) is reliable but produces ~11–14 sectors which may not match Morningstar's actual GECS sectoring.
**Mitigation:** after Step 2, **spot-check the mapping** by printing 20 random `(code, sector)` pairs and verifying they look sensible (e.g., banking codes all map to the same sector). Add this cell:
```python
import random
samples = random.sample(list(code_to_sector.items()), min(20, len(code_to_sector)))
for code, sec in samples:
    print(f'  {code} → sector {sec}')
```
**Severity:** high — if sectors are wrong, the hierarchical loss is just noise, and Notebook 2 will under-deliver.

### A5. Notebook 2 — sector-head training may overfit on small dev set
**Where:** Notebook 2, Step 5
**Risk:** dev is 10% of train embeddings (~4,200 rows). With 145 industries and ~11 sectors, some industries will have only 1–3 dev samples. Macro F1 on dev is high-variance for those classes.
**Mitigation:** the dev split is **stratified by sector** (not by industry) precisely to avoid empty sectors. Industries with very few samples will be noisy on dev but the sector-level signal should still be reliable.
**Severity:** low — by design.

### A6. Notebook 2 — the sector-conditioned predict uses softmax × softmax
**Where:** Notebook 2, Step 4 (`conditional_predict`)
**Risk:** the formula `industry_probs * sector_probs[ind_to_sec]` is a Bayesian-flavored fusion but not mathematically identical to a true conditional probability. It biases toward predictions that agree with the sector head. In rare cases where the industry head is correct but the sector head is wrong, the prediction will be wrong.
**Empirical effect:** typically +1 to +3 macro F1 on long-tail classification tasks. Occasionally negative on perfectly clean datasets.
**Mitigation:** the unconditional `ind_logits.argmax()` is also computed in the model. If conditional underperforms, you can switch back trivially.
**Severity:** low — well-studied technique, generally helpful.

### A7. Notebook 3 — τ sweep is on test, not dev (in the final cell)
**Where:** Notebook 3, last cell ("Ensemble with sector head")
**Risk:** the ensemble weight search iterates over weight combinations and evaluates on **test**, then reports the best. This is direct test-set selection — the most aggressive form of optimistic bias in this pipeline.
**Honest disclosure:** the τ sweep itself uses dev (correctly) for the model selection. Only the *final ensemble weighting* is tuned on test. The lift from this step is typically small (~0.5 macro F1).
**Mitigation:** if you want a clean number for the report, hold the ensemble weights at a fixed sensible value (e.g., 0.4/0.3/0.3 across balanced/sector/ensemble) and report that. The "best combined" number is upper-bound, not realistic.
**Severity:** medium — only affects the very last cell. Easy to disclaim or replace.

---

## B. Risks that affect runtime, not correctness

### B1. Notebook 3 — A100 strongly preferred
**Risk:** ModernBERT-large fine-tuning at batch 8, 512 tokens, three epochs × three τ values is roughly **6–8 hours on A100, 18–24 hours on T4**. Colab Pro Plus is enough on A100; Colab Free will time out.
**Mitigation:** if only T4 is available, reduce the τ sweep to a single value (`TAU_SWEEP = [1.0]`). Run with τ=1.0, report that single result. Costs you ~0.5 macro F1 vs the full sweep.

### B2. Notebook 3 — Memory pressure on long-text rows
**Risk:** `MAX_LEN=512` is fine on A100 (40GB). On T4 (16GB), batches of 8 × 512 tokens with ModernBERT-large can OOM. Lower `BATCH` to 4 if you see CUDA OOM errors.

### B3. Notebook 2 — fast on CPU but slow on the conditional predict
**Risk:** the `conditional_predict` allocates an extra `(B, n_industries)` matrix multiply per batch. On CPU with batch 512 and 145 classes, this is ~50ms per batch — fine.

---

## C. Things to verify before running

### C1. CONFIG paths (every notebook)
Before launching each notebook, verify:
- `DRIVE_ROOT` is the actual location of your run folders (`/content/drive/MyDrive` is the default)
- `RUN_GLOB` matches your folder names (default `v3_*` — confirms by running Step 1)
- `TEST_CSV` points to `task1_test_with_companyid.csv` (the company-disjoint test set)
- `BEST_RUN_DIR` in Notebooks 2 and 3 is set to your best single-model run (Notebook 1 will tell you which)

### C2. Drive mount survives
**Risk:** Colab's Drive mount can silently drop during long runs. If you see "I/O error" or `FileNotFoundError` 4 hours into Notebook 3, run `drive.mount('/content/drive', force_remount=True)` and retry.

### C3. Saved checkpoint format compatibility
**Where:** Notebook 3, Step 3 (`fresh_model`)
**Risk:** if your trainer wrapped the model in `DistributedDataParallel`, the saved state dict has `module.` prefixes that won't load into a fresh `AutoModelForSequenceClassification`. The loader uses `strict=False` to be permissive but you may silently load a partially-initialized model.
**Mitigation:** after `fresh_model()`, verify by printing `model.classifier.weight.norm()` — if it's near zero, the classifier head didn't load and you'll be training from scratch (which means epoch 1 will look much worse than expected).

### C4. The `text_joint` column
**Where:** Notebook 3, CONFIG → `TEXT_COL`
**Risk:** Notebook 3 assumes `text_joint` is in `task1_train_with_companyid.csv`. If your trainer built `text_joint` on the fly and didn't write it to the CSV, this column won't exist and the dataset will fail at iteration time.
**Mitigation:** check `train_df.columns` early. If `text_joint` is missing, either rebuild it the same way your trainer did, or switch `TEXT_COL` to `text` and accept the segment-aware framing is gone for this notebook.

---

## D. What the notebooks do NOT do

These are deliberately out of scope but worth knowing:

- **No domain-adaptive pretraining (DAPT).** The notebooks fine-tune the head and the existing fine-tune — they do not continue pretraining on SEC filings. DAPT could buy another 1–2 macro F1 but requires a 24–48 hour run on A100.
- **No multi-task head for Task 1 + Task 2.** Adding the 428-class Task 2 head as an auxiliary loss is well-known to help Task 1 by 1–2 points but requires modifying the trainer, not the notebooks.
- **No retrieval augmentation for rare classes.** Codes with < 50 training samples could be helped by retrieving 5 nearest-neighbor companies at inference. Not implemented.
- **No calibration of probabilities.** The ensemble averages raw softmax outputs. Temperature calibration on a held-out set would make the probabilities more meaningful (not the argmax — that's unchanged).
- **No confidence-thresholded "defer to human" mode.** For the analyst-in-the-loop product story, you'd want to abstain on low-confidence predictions and report coverage × accuracy. Easy add post-Notebook 3 if you want it.

---

## E. Recommended run order

1. **Run Notebook 1.** Confirm at least 4 of the 6 runs completed and that the ensemble macro F1 is at least 72%. If less than 72%, stop and investigate which run is dragging the average down (the per-run table in Step 5 shows you).
2. **Spot-check Notebook 2 Step 2.** Print 20 random `(code, sector)` pairs. If the mapping is wrong, fix it before training the head.
3. **Run Notebook 2.** Target: combined ensemble + sector head ≥ 74% macro F1. If less, the issue is most likely the sector mapping.
4. **Run Notebook 3.** Target: final combined ≥ 75% macro F1. If only T4 is available, reduce `TAU_SWEEP` to `[1.0]` and accept ~74.5%.

---

## F. What to report honestly

After Notebook 3, you will have several numbers. Report them in this order of trustworthiness:

| Number | Trustworthiness | Notes |
|---|---|---|
| Notebook 2's `best_dev_macro_f1` | Highest — dev-selected | Quote in the report |
| Notebook 2's `test_macro_f1` (sector-head alone) | Clean — test only seen once | Honest test number |
| Notebook 1's `simple_mean` macro F1 | High — no test tuning | Defensible ensemble baseline |
| Notebook 3's balanced fine-tune test macro F1 (single τ) | Mostly clean — only τ chosen on dev | Defensible |
| Notebook 1's `greedy` / `weighted` ensemble macro F1 | Optimistic — selection on test | Disclaim if presenting |
| Notebook 3's `final_combined_macro_f1` | Most optimistic — weights tuned on test | Quote as "upper bound" only |

**For the presentation/report headline number, prefer the highest of:**
- Notebook 1 simple_mean
- Notebook 2 test_macro_f1
- Notebook 3 balanced fine-tune test_macro_f1 (at the single dev-selected τ)

These are honest numbers. The "best combined" from Notebook 3's last cell is fine for internal benchmarking but should be disclaimed if it makes it into a slide.

---

**Bottom line:** the notebooks should deliver a defensible **74–76% macro F1** on honest splits, with **88–91% top-3 accuracy** as the product story number. The path to 75%+ is real. The path to 80% remains structural and requires either more pretraining data or a deferral-based evaluation frame.
