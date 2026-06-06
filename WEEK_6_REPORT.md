# MGT 599 Capstone — Weekly Progress Report

**Week:** Week 6 (final week before presentation)
**Reporting period:** May 11 – May 17, 2026
**Group:** 4
**Submitted by:** Akash Anipakalu Giridhar
**Submission date:** May 17, 2026

---

## 1. Summary

This week the team closed the gap between an inflated headline number and a defensible honest one. We diagnosed and remediated a data-leakage issue in our earlier evaluation, rebuilt the train/test pipeline on a company-disjoint basis, retrained our strongest transformer, and produced a reproducible baseline at **70.29% Macro F1** on the new clean evaluation. We also locked the foundation for next week's stretch work by shipping six parallel training variants and finalizing the presentation deck.

---

## 2. Quantitative outcomes

| Metric | Week 5 close | Week 6 close | Change |
|---|---|---|---|
| Best reported Macro F1 (Task 1) | 88.90% *(later shown to be leaked)* | 70.29% *(honest, company-disjoint)* | Revised down for integrity |
| ModernBERT-large dev Macro F1 (epoch 3) | 68.28% | **70.29%** | +2.01 pp |
| Industry accuracy | 69.5% | **71.4%** | +1.9 pp |
| Test rows with verified CompanyId | 0 (split lacked the key) | **10,535 / 10,717 (98.3%)** | New artifact |
| Train rows joined to CompanyId | 0 | **42,116 / 42,868 (98.2%)** | New artifact |
| Active parallel training runs | 0 | **6** | New |

---

## 3. Tasks completed

### 3.1 Data integrity — leakage audit and remediation
- Audited the cascade pipeline that had been reporting 88.9% Macro F1.
- Discovered that **97.2% of test rows had been seen by the model during training** because the original split was row-level random rather than company-disjoint. The same company's text appeared on both sides of the split.
- Documented the finding in `CASCADE_AUDIT.md` with the exact join logic, reproduction steps, and contaminated row counts.
- Rebuilt the split files using a LongProfile-prefix join (200 characters, with a 100-character fallback) to recover CompanyId on rows that had been stripped of it.
- Wrote `llm_finetuning/data/task1_test_with_companyid.csv` (10,535 / 10,717 = 98.3% joined) and `task1_train_with_companyid.csv` (42,116 / 42,868 = 98.2%). These are now the source of truth for every honest evaluation going forward.

### 3.2 Modeling — ModernBERT-large retraining on clean splits
- Re-ran ModernBERT-large training (`microsoft/modernbert-large`) on the company-disjoint splits.
- Selected epoch-3 checkpoint based on dev Macro F1 (70.29%); industry accuracy reached 71.4% on the held-out test set.
- Confirmed the long-tail error profile is concentrated in Diversified Conglomerates (GECS code 31030010), which alone accounts for the largest single contribution to Macro F1 loss.

### 3.3 Experimentation — six parallel variants launched
Six Colab notebooks were prepared and queued to explore the configuration space against the new baseline:
1. Baseline ModernBERT-large on raw text (seed 42)
2. Segment-aware text via `text_joint` field (seed 42)
3. Segment-aware text via `text_primary` field (seed 42)
4. Segment-aware text with revenue-share sample weighting (seed 42)
5. Distillation on raw text with teacher reasoning JSONL (DISTILL_WEIGHT = 0.3)
6. Variance / ensemble member — segment-aware joint text on seed 123

Each run saves checkpoints, top-5 predictions, and CLS embeddings to Google Drive for downstream ensemble work.

### 3.4 Library engineering — BreezeML
- Continued maintenance of the `breezeml` PyPI library (Akash A.G., author). The Level 2 hierarchical cascade extension (Sector → Industry Group → Morningstar Code) developed earlier in the term remains the architectural foundation of the V3 Meta-Ensemble.
- Confirmed five public releases (`v0.2.1` through `v0.2.5`) shipped during the capstone are stable and reproducible.

### 3.5 Deliverables for presentation
- Drafted full 15-slide presentation content matching the Dark Minimalist template palette (`#001514` background, `#FFFFFF` text, `#C2D076` lime accent).
- Wrote `PRESENTATION_CONTENT.md` with per-slide body, speaker notes, timing breakdown (10-minute target), rubric alignment, and chart generation prompts.
- Built `REFERENCE_DECK.pptx` as a layout/color reference for the team.
- Pre-wrote backup appendix slides (architecture diagram, top confusion class) and an FAQ covering the six most likely panel questions.

---

## 4. Challenges encountered

1. **Reporting a worse number on purpose.** The single largest decision this week was choosing to publish 70.29% honest over 88.9% leaked. It is uncomfortable to walk into a final presentation with a lower headline than we had a month ago, but it is the only defensible position.
2. **The 80% target is data-bound, not model-bound.** Audit analysis confirmed that 55.2% of training rows have inherent label ambiguity (multi-segment conglomerates with the same LongProfile but different codes per segment). Even a perfect single-code classifier combined with 60% multi-code accuracy mathematically caps Macro F1 at approximately 76%. The remaining headroom requires either an evaluation-frame change (Option A — decidable-subset) or a structural change (Option C — sector-conditioned head on transformer embeddings).
3. **Time pressure on parallel runs.** Six concurrent training jobs strain Colab Pro Plus session limits. Each notebook is checkpointing to Drive so partial results survive disconnections, but completing all six before the presentation is not guaranteed.

---

## 5. Plan for next week (Week 7 — post-presentation)

1. Deliver capstone final presentation on Monday, May 18, 2026.
2. Collect the six parallel variant results and select the best two for an ensemble.
3. Begin work on Option C (sector-conditioned head on ModernBERT-large embeddings) — the most promising legitimate path to 75–78% Macro F1.
4. Finalize Task 2 (428 sub-industry code) results and write the supporting documentation.
5. Open-source the company-disjoint split files and the audit script so the methodology is reproducible by future cohorts.

---

## 6. Reflection

The most valuable thing this week was not a model improvement — it was the audit. We taught ourselves that an unverified number is worse than no number at all. The honest 70.29% is a lower bar than the leaked 88.9%, but it is the bar from which every future improvement will be measured truthfully. That discipline, more than any specific architecture choice, is the work product I am proudest of from this capstone.

---

**Time spent this week:** approximately 38 hours
**Key artifacts produced:** `CASCADE_AUDIT.md`, `task1_test_with_companyid.csv`, `task1_train_with_companyid.csv`, `PRESENTATION_CONTENT.md`, `REFERENCE_DECK.pptx`, six configured Colab training notebooks
**Status:** On track for Monday presentation. Stretch work continues in parallel.
