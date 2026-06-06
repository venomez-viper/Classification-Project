# MGT 599 Capstone — Week 5 Report
**Group 4 | Akash Anipakalu Giridhar**
**Date: May 10, 2026**

---

## 1. Description of Work

### What We Were Trying to Achieve

The goal for Week 5 was to break past the ~68–69% Macro F1 ceiling that every model — TF-IDF, MiniLM, BGE, FinBERT, multi-encoder ensembles — converged to in Week 4. The diagnostic hypothesis from the Week 4 audit was clear:

> *The universal plateau is not a representation problem. It is an input-contamination problem. LongProfile concatenated with segment text creates many-to-many label mappings for the 35% of companies that are diversified conglomerates.*

Three concrete questions guided the week:

1. **Does removing LongProfile from the input unlock meaningful F1 gains?** (Lane A: segment-only baseline.)
2. **Does a hierarchy-aware transformer trained jointly on sector → group → industry beat a flat 145-class head?** (Strategic lane: DeBERTa-v3 multi-task on Colab GPU.)
3. **Does retrieval-augmented classification using the official GECS taxonomy as anchors add usable signal?** (V13 anchor injection completed.)

### Approach

The week split into two parallel tracks. The classical-ML team ran four model variants on the existing concatenated input to establish whether smaller architectural changes (subword features, larger vocab, class rebalancing, non-linear classifiers) could close the gap. The strategic track moved to Google Colab GPU for the first transformer fine-tune the project has attempted at scale.

**Team distribution (executable scripts in `docs/Week5_Team_Tasks.md`):**

| Member | Model | Task | Purpose |
|--------|-------|------|---------|
| Srilaxmi  | Linear SVM with word + character n-grams | Task 1 | Test whether subword signal helps rare codes |
| Vishal    | Logistic Regression, 100k vocab + trigrams | Task 1 | Test whether higher-capacity linear modeling helps |
| Subasree  | Linear SVM with `class_weight='balanced'` | Task 2 | Lift rare-subindustry F1 |
| Tserennad | Random Forest, 300 trees, max_depth 40    | Task 1 | Non-linear classical baseline |
| Akash (lead) | DeBERTa-v3-base, hierarchical multi-task heads, focal loss, AMP | Tasks 1 & 2 | Strategic transformer experiment on Colab T4 GPU |

**Hierarchical multi-task architecture (lead workstream):**

A single DeBERTa-v3-base encoder feeds three classification heads — sector (11 classes), industry group (55 classes), industry (145 classes) — trained with a weighted multi-task loss:

```
total_loss = 0.15 · CE(sector) + 0.15 · CE(group) + 0.70 · CE(industry)
```

The hierarchy is treated as a learning signal rather than a top-down cascade. Each level shares the encoder, which forces the representation to be useful at every depth and avoids the L1 → L2 → L3 error propagation that hurt the original cascade.

Key training configuration:
- Encoder: `microsoft/deberta-v3-base` (184M parameters)
- Sequence length: 512 tokens
- Effective batch size: 64 (per-device 4 with gradient accumulation 16)
- Optimizer: AdamW, weight decay 0.01
- Schedule: cosine with linear warmup (5% of total steps)
- Mixed precision: FP16 autocast with `GradScaler`
- Class weighting: sqrt-balanced on the leaf head only

**V13 follow-up — GECS official-taxonomy anchoring:**

Completed the implementation of label semantic anchoring. All 145 official Morningstar 2019 GECS industry definitions were parsed from the case-issued PDF, encoded with MiniLM and BGE, and added as 580 cosine-similarity features per sample (`MiniLM_seg × 145`, `MiniLM_long × 145`, `BGE_seg × 145`, `BGE_long × 145`). Stacked on top of the V8 mega-ensemble feature set, this produced a 123,469-dimensional input for a LinearSVC.

---

## 2. Summary of Findings

### Task 1 — Industry Classification

| Pipeline | Macro F1 | Accuracy | Top-10 pass |
|---|---|---|---|
| V10 calibrated stack (Week 4 best) | **69.09%** | 71.65% | 2/10 |
| V13 with GECS PDF anchors (Week 5) | 67.99% | 70.81% | 2/10 |
| V14 Retrieval-Augmented Classification | 66.04% | 68.69% | 1/10 |
| DeBERTa-v3 hierarchical (Colab, 2 epochs trained so far) | 44.49% (interim) | — | — |
| DeBERTa-v3 hierarchical (Colab, after resume attempts) | unstable | — | — |

**Key insight 1 — anchors didn't break through.** The GECS taxonomy similarity features added measurable signal but were drowned out by the ~122k TF-IDF features that dominate the input matrix. The official definitions are at semantic distances from real company descriptions that are very different from the empirical class prototypes we already had. The novel methodology survives as a documented contribution; the F1 effect was neutral.

**Key insight 2 — the DeBERTa fine-tune is mid-flight and unstable.** The hierarchical multi-task model achieved 44.49% Macro F1 after two epochs on the original training settings (focal loss with class weights + weighted sampler + LR 1e-5 + gradient checkpointing). Three recovery attempts in the second half of the week — each correcting an issue identified in the previous run — uncovered three real engineering problems with mixed-precision training in Colab's pinned environment:

1. **FP16 gradient unscaling error.** PyTorch's `GradScaler.unscale_` raised `ValueError: Attempting to unscale FP16 gradients` after the first gradient-accumulation step. Root cause: gradient checkpointing with `use_reentrant=True` (the legacy default) caused the recomputed backward pass to produce FP16 grads outside the autocast scope. The fix `gradient_checkpointing_kwargs={"use_reentrant": False}` was silently ignored by Colab's transformers fork. The workable fix was to disable gradient checkpointing entirely and halve the per-step batch to compensate.

2. **Double rebalancing collapse.** The first successful training pass — with the original `WeightedRandomSampler` + `class_weight='balanced'` + focal loss `gamma=2` — collapsed the resumed model from 44.49% to 5.45% in one epoch. Combining the sampler (which oversamples rare classes) with class weights in the loss (which weights them again) and gamma-2 focal focus produced rare-class gradients 10–50× the size of common-class gradients. The 44.49% model's representations were destroyed in one pass.

3. **Reset to vanilla training.** The textbook fix — plain `shuffle=True`, no `WeightedRandomSampler`, vanilla `CrossEntropyLoss`, sqrt-balanced weights on the leaf head only, LR 2e-6 — is being re-run at the time of writing. The next epoch will confirm whether the checkpoint is recoverable or requires a fresh fine-tune from the pretrained DeBERTa.

**Key insight 3 — the V10 calibrated stack remains the project's honest best.** Until DeBERTa stabilizes, the production candidate for Task 1 is V10 at 69.09% Macro F1 / 71.65% accuracy on the case-standard row-level split.

### Task 2 — Subindustry Classification

| Pipeline | Macro F1 | Weighted F1 |
|---|---|---|
| Linear SVM with balanced class weights (Subasree, Week 5) | (pending team result) | (pending team result) |
| Hierarchical roll-up plan from Task 1 | scaffolding ready | scaffolding ready |

The Task 2 architecture for the final delivery uses the deterministic Task 1 → Task 2 mapping as a hard inference constraint: predict the Task 1 industry code, then restrict Task 2 predictions to the ~3 business-activity codes that roll up into that industry. This is the right structural use of the case's stated one-to-many relationship and avoids treating Task 2 as an isolated 450-class flat problem.

### Broader Insight

Week 5 confirmed three things and changed our priors on a fourth:

- **Confirmed:** The 68–69% ceiling is real for the classical + sentence-embedding family on the contaminated input.
- **Confirmed:** Hierarchy-aware modeling is the right architectural direction. The DeBERTa multi-task structure is sound; the instability is in training dynamics, not in the design.
- **Confirmed:** Method documentation matters — every collapse this week was caught and explained, not just absorbed. The audit discipline from Week 4 has carried into Week 5.
- **Changed:** We previously expected segment-only inputs to be the dominant lever. The DeBERTa runs have not yet given us a clean answer because the training collapses derailed the validation. The hypothesis test moves into early Week 6.

---

## 3. Supporting Outputs

| File | Contents |
|------|----------|
| `colab/finbert_finetune.ipynb` | Colab notebook for the Week 4 FinBERT baseline (61.84% Macro F1) |
| `scripts/train_cascade_v13_gecs_anchors.py` | V13 — GECS official-taxonomy anchor injection + class prototypes |
| `scripts/train_cascade_v14_rac.py` | V14 — Retrieval-Augmented Classification with KNN over training and taxonomy |
| `scripts/parse_gecs_taxonomy.py` + `scripts/fill_missing_gecs.py` | PDF parser that extracted all 145 industry definitions from the Morningstar 2019 GECS reference |
| `gecs_taxonomy.json` | Structured taxonomy (mstar_code → sector_name + industry_name + official_description) |
| `models_v13/training_summary.json`, `models_v14/training_summary.json` | Reproducible results for the week's runs |
| `docs/Week5_Team_Tasks.md` + `.docx` | Per-member executable scripts and results table |
| `docs/Initial_Proposal.md` + `.docx` + `Initial_Proposal_McKinsey.docx` | First formal proposal of the project, including the Week 1–5 code journey |
| `docs/proposal_exhibits/*.png` | Six chart exhibits used in the proposal (performance journey, GECS hierarchy, top-10 breakdown, contamination diagnostic, architecture diagram, cumulative-gain plan) |
| `PROJECT_JOURNEY.md` and `CASCADE_AUDIT.md` | Running project narrative and the leakage audit document |

The Colab notebook outputs (model weights, predictions, embeddings) for the DeBERTa hierarchical run are saved under `htc_outputs/` and will be re-pulled to local after the recovery run stabilizes.

---

## 4. Reflection

### Challenges Encountered

**Challenge 1: Mixed-precision training instability on Colab.**
Three separate FP16-grad errors surfaced over the recovery attempts (`use_reentrant`, sampler+weights interaction, scaler state mismatch on resume). Each required a small surgical fix and a re-run. The lesson is that resuming a fine-tuned transformer is significantly more fragile than initial training — optimizer state, scaler state, and the loss configuration all have to remain consistent between runs. Future Colab runs will save the full training state (model + optimizer + scaler + scheduler + best-F1) instead of weights only.

**Challenge 2: GECS anchors got diluted in the feature stack.**
The 580 anchor features represented less than 0.5% of the 123,469-dimensional input. LinearSVC weights them by their gradient contribution, which gave the high-cardinality TF-IDF features structural dominance. The right way to use the anchor signal is either as a separate scoring branch (a calibrated similarity score) or by training a model with much smaller TF-IDF and letting embeddings + anchors dominate. This is queued for Week 6.

**Challenge 3: The 88.90% leakage diagnosis is right but not yet "paid back."**
We have an honest 69%. Other teams may be presenting higher numbers — almost certainly with the same kind of contamination we caught in ourselves. There is a real concern that our honesty looks like underperformance until the methodology audit is read alongside the F1 number. The Week 6–8 plan responds by making the audit a foreground deliverable (a one-page summary slide) rather than an appendix.

**Challenge 4: My fault, documented.**
Two of the model collapses this week were the result of changing the wrong hyperparameter at the right time. Specifically, when the FP16 error surfaced, the focus shifted to gradient flow plumbing and the loss configuration was not re-validated for its interaction with the sampler. The post-mortem fix — disabling either the sampler or class weights but not both — is now codified as a project invariant.

### Next Steps (Week 6)

1. **Finish the DeBERTa recovery run** with the vanilla settings (plain shuffle, vanilla CE, LR 2e-6, sqrt-balanced leaf weights). Capture the pre-training sanity F1 to verify the loaded checkpoint is intact.
2. **Run the segment-only experiment cleanly** (Lane A from Week 5). If segment-only with the V8 hybrid stack hits 73%+, the contamination hypothesis is confirmed and we re-launch DeBERTa on segment-only inputs.
3. **Add Distribution-Balanced or DCAL loss** to the leaf head on the next DeBERTa run for explicit rare-class macro F1 lifting.
4. **Build Task 2 baseline** with the hierarchical roll-up constraint. Target: 50%+ Macro F1 on `task2_clean.csv` using the predicted Task 1 industry as a filter on candidate subindustries.
5. **Demo cleanup.** Replace `server_legendary.py`'s softmax-on-margin pseudo-confidence with `CalibratedClassifierCV` probabilities plus a top-3 alternatives panel.
6. **Begin error analysis** for the final write-up — generate confusion matrices for the worst-performing classes and document the residual conglomerate confusion pattern as a governance recommendation.

---

*Submitted by Group 4, MGT 599 Capstone, DePaul University Chicago.*
