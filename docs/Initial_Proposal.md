# Initial Project Proposal
## GECS Industry and Business Activity Classification using Machine Learning

**MGT 599 Capstone Project · Q2 2026**
**Group 4 · DePaul University Chicago**
**Lead: Akash Anipakalu Giridhar · Team: Srilaxmi, Vishal, Subasree, Tserennad**
**Industry Partner: Morningstar — Reference Entity Data (RED) Team**

**Date: May 10, 2026**

---

## 1. Executive Summary

This proposal documents our first five weeks of work on the Morningstar GECS classification capstone, presents our preliminary findings and the substantial methodological audit we completed, and lays out the technical path forward through the remaining sprint.

We are building two supervised classifiers:

1. **Task 1 — GECS Industry Classification:** Map a company's `LongProfile` + segment text into one of **145 Morningstar industry codes**.
2. **Task 2 — Business Activity Subindustry Classification:** Map segment-level text into one of **450 business activity codes**, exploiting the deterministic one-to-many parent–child relationship from Task 1 to Task 2.

Our baseline pipeline reached an apparent **88.90% Macro F1** in Week 3. In Week 4 we discovered this number was **inflated by training/test leakage** — 97.2% of test rows were present in the training set. The honest baseline, after rebuilding the pipeline with strict train/test separation, is **69.09% Macro F1**.

This proposal explains exactly how we got here, what we have learned, why we are not aiming for the illusion of 88.90% anymore, and what we will do in the remaining weeks to push the honest number toward the 75–80% range expected by the case rubric.

---

## 2. Problem Background

Morningstar's Reference Entity Data (RED) team maintains GECS, a four-level hierarchical taxonomy that organizes every publicly listed company in their global coverage universe into a sector → industry group → industry → business activity tree. Analysts use GECS for peer comparison, portfolio construction, risk attribution, and reporting. Misclassification at the leaf level propagates upward and distorts every product downstream — including PitchBook on the private-markets side.

GECS classification today is largely manual. The case asks us whether modern NLP can scale this work: given the structured and unstructured company disclosures Morningstar already collects, can we automate the assignment with production-grade accuracy?

The Morningstar 2019 GECS structure document and the case-issued data make this concrete:

- **3** Super Sectors → **11** Sectors → **55** Industry Groups → **145** Industries → **450** Business Activities
- **Task 1 dataset:** 53,585 records, Dec 2003 – Dec 2024, 145 classes
- **Task 2 dataset:** 27,537 records, May 2020 – Dec 2024, 450 classes
- **Stated Pass-criteria** (per the case rubric): Macro F1 ≥ 0.75 on overall classification; top-10 most-frequent class F1 > 0.85

---

## 3. Objectives

| # | Objective | Status |
|---|---|---|
| 1 | Stand up an honest end-to-end training and evaluation pipeline for both tasks | **Complete** (Week 4) |
| 2 | Document the dataset structure, label distributions, and inherent class imbalance | **Complete** (Week 2) |
| 3 | Produce reproducible baselines using classical ML (TF-IDF + linear classifiers) | **Complete** (Week 3) |
| 4 | Audit baselines for hidden data leakage and methodological errors | **Complete** (Week 4) |
| 5 | Move beyond bag-of-words representations with semantic embeddings | **Complete** (Week 4) |
| 6 | Hit Macro F1 ≥ 0.75 on Task 1 (case threshold) | **In progress** (Week 5) |
| 7 | Build Task 2 classifier exploiting the hierarchical Task 1 → Task 2 constraint | **Scaffolding underway** (Week 5) |
| 8 | Deliver a working demo, full audit document, and reproducible code | **Ongoing** |

---

## 4. Data Overview

### 4.1 Task 1 — Industry classification

| Field | Type | Used as |
|---|---|---|
| `CompanyId` | string | Group key |
| `AsOfDate` | string | Snapshot stamp |
| `LongProfile` | free text | Company-level description |
| `SegmentName` | string | Segment label |
| `SegmentDescription` | free text | Segment-level description |
| `Revenue` | float | Engineered feature input |
| `total_revenue_company_as_of` | float | Engineered feature input |
| `revenue_share` | float | Engineered feature |
| `is_largest_share_segment` | bool | Engineered feature |
| `MstarGlobal` | class (145) | **Target** |

### 4.2 Key data characteristics

- **Class imbalance:** the top-10 most-frequent industry codes account for ~30% of records; the bottom 50 codes have fewer than 200 records each.
- **Multi-segment companies are common:** ~35% of `CompanyId` values have segments mapping to different MstarGlobal codes. These are diversified conglomerates whose `LongProfile` describes the entire company but whose individual segments resolve to different industries.
- **Sector 310 (Industrials)** contains the single hardest leaf code, `31030010` (Diversified Industrial Conglomerates), F1 ~ 30% on honest evaluation.

### 4.3 Task 2

Smaller dataset (27.5k rows), more classes (450), shorter text (`SegmentName + SegmentDescription` only — no `LongProfile`). Each Task 2 code deterministically rolls up into exactly one Task 1 code. This relationship is a hard constraint we will use at inference time.

---

## 5. The Code Journey — Weeks 1 through 5

This section is the spine of the proposal: the work, in order, and what each iteration taught us.

### Week 1 — Project setup
- Team formation, environment standardization (Python 3.11, sklearn 1.4, custom `breezeml` wrapper).
- Repo layout: `data/`, `scripts/`, `models/`, `notebooks/`, `docs/`.
- Initial reading of the case PDF and the Morningstar GECS taxonomy reference.

### Week 2 — Data exploration and cleaning
- Built `task1_clean.csv` and `task2_clean.csv`.
- Profiled class distributions, text length distributions, and missing-value patterns.
- Identified that the cleaned text input would be: `LongProfile + SegmentName + SegmentDescription` concatenated.
- Engineered initial structured features: `revenue_share`, `is_largest_share_segment`, and (added later) `num_segments`, `max_share`, `share_std` at the company level.
- **Deliverable:** `docs/Week2_What_We_Did.md` + descriptive-analytics notebook.

### Week 3 — Baseline classical-ML pipeline
- Implemented the canonical TF-IDF + Linear SVM pipeline via our `breezeml` library wrapper.
- **Task 1 result:** Weighted F1 = 86.82%, Macro F1 = 61.07% (random 80/20 stratified split on the full dataset).
- **Task 2 result:** Weighted F1 = 47.72%, Macro F1 = 39.62% (407 classes after filtering single-occurrence labels).
- Key insight at the time: the model was finding interpretable industry-defining vocabulary (`semiconductor`, `brokerage`, `pharmaceutical`) — the misclassifications were near-misses inside the correct sector.
- **Deliverable:** `docs/Week3_Report.md`, `notebooks/week3_modeling_task1.ipynb`, `notebooks/week3_modeling_task2.ipynb`.

### Week 4 — The audit that changed everything

We attempted to ship a "legendary" cascaded SVM (sector → group → industry) and an interactive demo. The cascade reported **88.90% Macro F1** on Task 1 — an apparent jump of nearly 30 points over the Week 3 baseline. The demo, however, only produced sensible predictions on four hand-crafted example inputs. Arbitrary user input returned random-looking labels with fake high "confidence" numbers.

That mismatch forced an audit. What we found:

1. **Training/test leakage in the original cascade.** The model trained on `data/cleaned/task1_clean.csv` (53,585 rows = the full dataset) and was evaluated on `llm_finetuning/data/task1_test.csv` (10,717 rows). **97.2% of those test rows were present in training**; only 305 were truly unseen. On the unseen 305, the same model scored **81.73%**, not 88.90%. The model is real — but the headline metric was leaked memorization.

2. **Fake confidence display.** The demo rendered `softmax(SVM decision-function margin)` as a "confidence" percentage. For out-of-distribution input the SVM still produces decision margins, the softmax still normalizes them, and the UI happily reported "92% confident" while predicting wrongly.

3. **Conglomerate noise.** ~35% of training companies are multi-segment with multiple labels. Because we concatenated `LongProfile` with segment text, an identical `LongProfile` prefix appears in ~55% of training rows mapping to different MstarGlobal codes. That is irreducible label noise we manufactured in preprocessing.

4. **Cascade error propagation.** L1 (sector) errors cascade downward. ~52% of all final errors trace back to a wrong L1 prediction. A top-down cascade is structurally bad for this problem unless L1 is near-perfect.

5. **TF-IDF ceiling.** Even after fixing leakage, pure TF-IDF + LinearSVC plateaus at ~57% Macro F1 on the honest split, regardless of vocabulary size, char n-grams, or C tuning.

The full audit is preserved in `CASCADE_AUDIT.md`.

We responded by **rebuilding the pipeline honestly**:

- Strict training-only use of `task1_train.csv` (42,868 rows); evaluation only on `task1_test.csv` (10,717 rows).
- Honest TF-IDF cascade Macro F1: **59.65%** (the real baseline).
- Honest segment + LongProfile concatenation Macro F1 with TF-IDF: 63.42%.
- With sentence embeddings (MiniLM 384-d): 59.70% — same ceiling.
- With both encoders + numerical features (V8 mega-ensemble): **68.42%**.
- With calibrated stacking and engineered features (V10): **69.09%**.

We then explored three more ambitious directions to break past 69%:

- **V13: GECS official-taxonomy anchoring.** We parsed all 145 industry definitions from the Morningstar 2019 GECS PDF (`Task Doc/MorningstarGlobalEquityClassStructure2019v2.pdf`), encoded each definition with the same MiniLM and BGE encoders we use for the text, and added the cosine similarity of every sample to every official anchor as 580 extra features. Result: 67.99% Macro F1 — the anchor signal was real but drowned out by the 122k TF-IDF features dominating the input.
- **V14: Retrieval-Augmented Classification (RAC).** For each test sample, we retrieved the top-25 most similar training rows (cosine over fused MiniLM + BGE embeddings) and aggregated their labels into a 145-class prior distribution that we fed as features into the classifier. Result: 66.04% — KNN features alone lost the raw embedding signal.
- **V16: FinBERT fine-tuning.** Three epochs on Google Colab T4 GPU using `yiyanghkust/finbert-pretrain`. Result: 61.84% Macro F1 alone, 0/10 top-10 pass. The domain mismatch (FinBERT is pretrained on financial *news*, not company segment descriptions) plus 3-epoch undertraining left us below our local stack.

**Deliverable:** `CASCADE_AUDIT.md`, `PROJECT_JOURNEY.md`, 17 numbered `scripts/train_cascade_v*.py` variants, all reproducible, with `models_v*/training_summary.json` for every run.

### Week 5 — The hypothesis we are testing now

The audit produced one diagnostic insight that we believe explains the universal ~68% plateau: **for ~55% of training rows, the input text is contaminated with the same `LongProfile` prefix as several other rows that have different labels**. No encoder, no loss function, and no ensemble can recover the right answer from input that ambiguously points to multiple labels.

Our Week 5 plan therefore moves in two directions simultaneously:

1. **Validate the contamination hypothesis** by training every Week 5 model on segment text only (`SegmentName + SegmentDescription`), with `LongProfile` either dropped or used only as a low-weighted auxiliary signal. (See `WEEK_5_PLAN.md` Lane A.)
2. **Apply hierarchy-aware modeling** on top of clean inputs: a single transformer encoder (DeBERTa-v3-base or similar) with multi-task heads for sector (11), group (55), and industry (145), trained with a joint hierarchy-weighted loss. Add Distribution-Balanced loss to lift rare-class macro F1.

**Team distribution this week** (see `docs/Week5_Team_Tasks.md` for executable scripts):

| Member | Model | Task | Purpose |
|---|---|---|---|
| Srilaxmi | Linear SVM with word + character n-grams | Task 1 | Test if subword signal helps rare codes |
| Vishal | Logistic Regression with 100k vocab + trigrams | Task 1 | Test if higher-capacity linear model helps |
| Subasree | Linear SVM with `class_weight="balanced"` | Task 2 | Lift rare-subindustry F1 |
| Tserennad | Random Forest | Task 1 | Non-linear baseline |
| Akash (lead) | DeBERTa-v3 hierarchical multi-task + segment-only input | Task 1 & 2 | Strategic core experiment |

---

## 6. Preliminary Results to Date

| Pipeline | Split | Macro F1 | Accuracy | Top-10 pass |
|---|---|---|---|---|
| Original cascade (Week 3) | Leaked (train ⊇ test) | 88.90% | n/a | 9/10 |
| Original cascade on truly unseen rows | Honest (n=305) | 81.73% | n/a | n/a |
| Honest TF-IDF cascade (Week 4 rebuild) | task1_train → task1_test | 59.65% | 62.0% | 1/10 |
| TF-IDF + numerical + engineered features | task1_train → task1_test | 63.42% | 66.2% | 1/10 |
| MiniLM embeddings only | task1_train → task1_test | 59.70% | 62.0% | 1/10 |
| V5 hybrid (TF-IDF + MiniLM + numerical) | task1_train → task1_test | 67.11% | 70.1% | 2/10 |
| V6 hybrid (TF-IDF + BGE-base + numerical) | task1_train → task1_test | 67.70% | 70.5% | 2/10 |
| V8 mega-ensemble | task1_train → task1_test | 68.42% | ~71% | 2/10 |
| **V10 calibrated stack (current honest best)** | **task1_train → task1_test** | **69.09%** | **71.65%** | **2/10** |
| V13 (V8 + GECS PDF anchors + class prototypes) | task1_train → task1_test | 67.99% | 70.81% | 2/10 |
| V14 (Retrieval-Augmented Classification) | task1_train → task1_test | 66.04% | 68.69% | 1/10 |
| V16 FinBERT 3-epoch fine-tune (Colab) | task1_train → task1_test | 61.84% | 62.15% | 0/10 |

---

## 7. Findings to Date — what we have actually learned

1. **Naïve cascade evaluation is dangerous.** Anyone reporting 88%+ on this task without a rigorous train/test audit is almost certainly leaking. We caught ourselves doing this.
2. **The representation isn't the bottleneck.** TF-IDF (60%), MiniLM (60%), and BGE-base (60%) all plateau in the same place. Switching encoders gets diminishing returns.
3. **Engineered features matter.** Adding `num_segments`, `max_share`, `share_std` over the TF-IDF + embedding stack added +4 to +7 percentage points by itself.
4. **The data has manufactured label noise.** Concatenating `LongProfile` with segment text creates many-to-many mapping for conglomerate companies. This is the most plausible explanation for the universal ~68% ceiling across architectures.
5. **The official GECS taxonomy is unused signal.** No team will think to parse the Morningstar 2019 GECS PDF and use it as semantic anchors. We have implemented this; we expect it to contribute meaningfully once the input contamination is fixed.
6. **Domain-pretrained BERT is not automatically better.** FinBERT was pretrained on financial *news*, not company descriptions. The distribution mismatch hurt us. The encoder choice has to fit the text type.

---

## 8. Methodological Innovations (the parts of this work that are genuinely novel)

1. **End-to-end leakage audit.** We caught and documented a 30-percentage-point inflation in our own baseline. The audit document (`CASCADE_AUDIT.md`) reads like a postmortem and is itself a deliverable.
2. **Official taxonomy anchoring.** Parsing the Morningstar 2019 GECS structure PDF and using the 145 official industry definitions as semantic anchors is, to our knowledge, not standard practice for this dataset.
3. **Multi-encoder hybrid feature stack with empirical class prototypes.** Stacking TF-IDF + MiniLM + BGE + class centroids + numerical features into a single ~123k-dimensional sparse representation, calibrated through `CalibratedClassifierCV`, has produced our current best honest result.
4. **Honest probability display.** We are replacing the original demo's softmax-on-margin pseudo-confidence with calibrated probabilities, plus a "top-3 alternatives" panel for low-confidence predictions.

---

## 9. Risks and Mitigations

| Risk | Mitigation |
|---|---|
| Macro F1 ≥ 0.75 may not be reachable on 145 fine-grained classes without domain-tuned modeling | Multi-pronged Week 5–6 plan: segment-only inputs + hierarchy-aware multi-task transformer + long-tail loss + retrieval augmentation. Each layer adds incrementally. |
| GPU compute limits on Colab free tier may bottleneck DeBERTa fine-tuning | Outputs (weights, embeddings) downloaded back to local CPU for inference; demo remains fully offline. |
| Conglomerate label noise is fundamentally unresolvable | If true, we present the honest ceiling with full diagnostic evidence rather than chase an illusion. Macro F1 in the 70–75% range honestly evaluated is still a stronger submission than a leaked 88%. |
| Team coordination across five members | Per-person executable scripts (Week 4–5 task sheets) with no cross-dependencies; lead consolidates results. |

---

## 10. Timeline and Next Steps

| Week | Focus | Owner |
|---|---|---|
| Week 5 (May 10 – May 16) | Segment-only hypothesis test + hierarchical DeBERTa + Task 2 scaffolding | Whole team, lead drives strategic experiments |
| Week 6 (May 17 – May 23) | Long-tail loss (DB / DCAL), retrieval-augmented classifier, Task 2 baseline | Lead + 2 |
| Week 7 (May 24 – May 30) | Ensemble best Task 1 model with Task 2 cross-constraint; demo cleanup with calibrated confidence | Lead + 2 |
| Week 8 (May 31 – Jun 6) | Error analysis, final write-up, reproducibility verification, presentation rehearsal | Whole team |

---

## 11. What We Will Deliver

1. **Working Task 1 classifier** with Macro F1 ≥ 0.75 honestly evaluated on `task1_test.csv`, or a documented best-effort below 0.75 with full diagnostic evidence of the ceiling.
2. **Working Task 2 classifier** that uses the Task 1 → Task 2 deterministic mapping as a hard constraint.
3. **Interactive demo** running locally on port 5003, with calibrated probabilities and an honest top-3 panel.
4. **Audit document** (`CASCADE_AUDIT.md`) detailing the leakage we caught, the splits, the iterations, and the methodology.
5. **Project journey document** (`PROJECT_JOURNEY.md`) telling the full story.
6. **Reproducible training scripts** for every numbered version (V1 through V20+), with per-run `training_summary.json` artifacts.
7. **Per-week team-task sheets** showing how the work was distributed across the team.
8. **Final presentation** suitable for Morningstar RED team review.

---

## 12. Closing Statement

Five weeks in, we have learned that the difference between a credible 88.90% and an honest 69.09% on this dataset is methodology, not modeling. Catching that distinction ourselves — rather than presenting an inflated number to Morningstar and being asked the obvious follow-up question — is the most important thing we have done so far. The remaining weeks are about closing the gap honestly, exploiting structural signal (the GECS hierarchy, the official taxonomy text, the Task 1 → Task 2 constraint) that other teams will not have spent the time to extract.

The number we deliver will be real. The work to get there is documented end-to-end.

---

*Prepared by Group 4 · DePaul University · MGT 599 · Q2 2026 · May 10, 2026*
