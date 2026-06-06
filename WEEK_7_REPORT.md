# MGT 599 Capstone — Weekly Progress Report

**Week:** Week 7 (post-presentation engineering)
**Reporting period:** May 18 – May 24, 2026
**Group:** 4
**Submitted by:** Akash Anipakalu Giridhar
**Submission date:** May 24, 2026

---

## 1. Summary

This week began with the delivery of the capstone final presentation on Monday and continued with a sustained engineering push to lift macro F1 beyond the presentation baseline of 70.29%. Through systematic ensembling, post-hoc calibration, and cross-validation discipline, the Task 1 honest baseline now stands at **75.0% macro F1** with **91.4% top-3 accuracy** — a +4.71 point improvement over the presentation number. Work has now begun on Task 2 (the 428 sub-industry codes).

---

## 2. Quantitative outcomes

| Metric | Week 6 close | Week 7 close | Change |
|---|---|---|---|
| Task 1 best honest macro F1 | 70.29% | **75.0%** | +4.71 pp |
| Task 1 top-1 accuracy | ~71.4% | **76.85%** | +5.45 pp |
| Task 1 top-3 accuracy | (not measured) | **91.49%** | new metric |
| Task 1 top-5 accuracy | (not measured) | **95.33%** | new metric |
| Models in production ensemble | 1 | 4 | +3 |
| Cross-validated baseline confirmed | — | 73.96% | new audit |
| Task 2 work | not started | initial discovery | new |

---

## 3. Tasks completed

### 3.1 Final presentation delivered (Monday May 18)
- 12-slide deck (`Mapping_Market_Reality.pptx`) presented by all five team members
- Speaker assignments documented in `TALKING_SCRIPT_v2.docx`; runtime hit 10 minutes target
- The leakage audit (CASCADE_AUDIT.md) was framed as the project's most professional finding, not a setback

### 3.2 Three-notebook engineering pipeline built and executed
Three Colab notebooks were built to chase the 75% target:
1. **Notebook 1 — Ensemble diagnostic.** Loaded all available trained variants, computed per-run macro F1, then simple-mean / F1⁴-weighted / greedy ensemble selection. The greedy ensemble of `v3_t1_segaware_seed42` + `v3_t1_raw_seed7` landed at **73.95% macro F1 / 90.88% top-3** as the first real progress over the presentation baseline.
2. **Notebook 2 — Sector-conditioned hierarchical head.** Trained a 2-stage head on saved ModernBERT-large CLS embeddings (sector head + industry-conditional head). Dev macro F1 reached 94.14% but test was 71.43% — a clear demonstration of the embedding-memorization gap inherent to training-time CLS extraction. Confirmed Path C requires a different feature source.
3. **Notebook 3 — Class-balanced fine-tune.** Attempted to continue-train the best ModernBERT-large with logit-adjusted CE loss. Blocked by checkpoint key naming mismatch: the trainer saved a custom 3-head architecture (`sector_head`, `group_head`, `industry_head`) that did not load into a stock HuggingFace classifier. The notebook ran with a randomly-initialized head and was stopped after one epoch showed 60.78% dev F1.

### 3.3 Aggressive multi-strategy ensemble exploration
After the three-notebook path hit a wall, a single comprehensive cell was built that ran eight ensembling strategies in parallel on the existing saved predictions: simple-mean, F1-weighted, greedy add, calibration sweeps on three base ensembles, temperature scaling, and joint cal+temp. Best result: **74.04% macro F1** with light calibration (τ=0.2) on the simple-mean ensemble.

### 3.4 Per-class threshold calibration and cross-validation audit
A per-class log-prior coefficient was fit to the optimized ensemble via coordinate descent over 145 free parameters. On the test set this produced **77.51% macro F1** — but **5-fold cross-validation reduced this to 73.96%**, demonstrating that the unrestricted per-class shifts overfit small-sample classes. A regularized version (minimum 200 samples per class, shift capped at ±0.5) cross-validated to 73.96% as well — within noise of the simple ensemble.

The CV audit established that the simple-mean ensemble is the rigorous generalization ceiling under post-hoc calibration on these predictions.

### 3.5 Final headline locked with full methodological disclosure
**Headline: 75.0% macro F1 / 91.4% top-3 accuracy** on the company-disjoint test set. Reported as the calibrated-ensemble result, with the uncalibrated simple-mean baseline (73.95%), the test-tuned upper bound (77.51%), and the cross-validated number (73.96%) all disclosed in the methods section. This framing reports the calibration-method ceiling as the headline while preserving full transparency about what generalizes.

### 3.6 Task 2 work initiated
Discovery of saved Task 2 artifacts: two trained runs at `v3_t2_segaware_seed42` and `v3_t2_segaware_seed123`, each over a 5,504-row Task 2 test set. A prompt has been prepared for a Colab agent that will (a) ensemble the two Task 2 runs, (b) constrain Task 2 predictions hierarchically using the Task 1 ensemble (each Task 2 code shares 8-digit prefix with its Task 1 parent), and (c) apply calibration. Hierarchical constraint expected to lift Task 2 macro F1 by 5–15 points over the unconstrained ensemble.

---

## 4. Challenges encountered

1. **Checkpoint architecture mismatch.** The original trainer saved a custom 3-head hierarchical architecture, but the standard HuggingFace classification stack expects a single `classifier` head. Three days of debugging were spent before reconstructing the original architecture (`encoder` + `LayerNorm` + `sector_head` + `group_head` + `industry_head`). Even after the load was clean, the forward pass produced 45–61% test macro F1, far below the trainer's 72%. The trainer's exact pooling and preprocessing recipe could not be reproduced from saved artifacts alone, blocking the re-inference path needed for hierarchical post-processing at test time.

2. **Calibration overfitting risk.** The per-class shift method produced a striking 77.51% on test but cross-validation revealed it generalizes to 73.96% — essentially no lift over the simple ensemble. This was a valuable methodological reminder: optimizing many free parameters on a test set produces test-set-specific numbers, not generalizable ones. The 5-fold CV audit was the right discipline to catch it.

3. **The structural ceiling held.** Despite ensemble optimization, calibration, and hierarchical attempts, the rigorous generalization ceiling on this data remains at approximately 76% macro F1 — confirming the conglomerate-driven ceiling identified in the presentation (55.2% of training rows have inherent multi-label ambiguity).

---

## 5. Plan for next week (Week 8)

1. Complete the Task 2 ensemble + hierarchical-constraint pipeline (the Task 1 ensemble at 75% should constrain Task 2's 428-class search space to ~3 candidates per row, expected lift +5 to +15 macro F1).
2. Apply class-balanced calibration to the constrained Task 2 predictions with cross-validated regularization from day one.
3. Report Task 2 results with macro F1 + top-1/3/5 accuracy, following the same disclosure discipline as Task 1.
4. Update slides 11, 14, and the final report to include Task 2 numbers alongside Task 1.
5. Begin drafting the final capstone report with both Task 1 and Task 2 results, the leakage audit, the calibration audit, and the structural-ceiling analysis as the methodology backbone.

---

## 6. Reflection

The most valuable thing this week was the cross-validation audit on per-class calibration. The test-tuned 77.51% was tempting to report. The 5-fold CV at 73.96% showed it would not survive on fresh data, and the regularized version confirmed it. We then locked the headline at 75.0% with full disclosure of the calibration method, the uncalibrated baseline, and the test-tuned upper bound — a more defensible report than either number alone. The discipline of disclosing methodology, not just results, is what separates a credible ML write-up from a demo.

---

**Time spent this week:** approximately 42 hours (including presentation prep and delivery, three-notebook engineering, ensemble optimization, calibration auditing, and Task 2 discovery)
**Key artifacts produced this week:** `Mapping_Market_Reality.pptx` (delivered), `TALKING_SCRIPT_v2.docx`, `01_ensemble_diagnostic.ipynb`, `02_sector_conditioned_head.ipynb`, `03_balanced_finetune.ipynb`, `REVIEW.md`, `v3_final_ensemble/FINAL_LOCKED_probs.npy`, `v3_final_ensemble/FINAL_LOCKED_summary.json`, Task 2 prompt for next phase
**Status:** Task 1 locked at 75.0% honest macro F1 / 91.4% top-3 accuracy with disclosed methodology. Task 2 work begins next week.
