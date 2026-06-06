# MGT 599 Capstone — Week 5 Plan

**Sprint dates:** May 10 – May 16, 2026
**Goal:** Break past the 68% Macro F1 plateau on Task 1 by addressing the root cause we identified in Week 4, then layer hierarchy-aware modeling on top of clean inputs.

---

## 1. Where Week 4 left us

| Approach | Macro F1 | Accuracy | Top-10 pass |
|---|---|---|---|
| TF-IDF cascade (honest) | 59.65% | 62.0% | 1/10 |
| V8 mega-ensemble (TF-IDF + MiniLM + BGE + numerical) | 68.42% | ~71% | 2/10 |
| V10 calibrated stack | **69.09%** | 71.65% | 1/10 |
| V13 (V8 + GECS taxonomy anchors + class prototypes) | 67.99% | 70.81% | 2/10 |
| V14 (Retrieval-Augmented Classification) | 66.04% | 68.69% | 1/10 |
| FinBERT fine-tuned (Colab, 3 epochs) | 61.84% | 62.15% | 0/10 |

**Best honest result: 69.09% Macro F1.** Still ~6pp short of the 75% case target, ~16pp short of the 85% stretch goal.

---

## 2. The root cause we found (Week 4 audit)

Every model so far is trained on rows where the input text is built by **concatenating LongProfile + SegmentName + SegmentDescription**.

For a conglomerate company with 3 segments having 3 different MstarGlobal codes, this produces:

```
Row 1: [same LongProfile] + Segment A text  →  Code X
Row 2: [same LongProfile] + Segment B text  →  Code Y
Row 3: [same LongProfile] + Segment C text  →  Code Z
```

The classifier sees **identical text prefixes mapping to different labels**. 35% of companies in the dataset are multi-code conglomerates, which means **~55% of training rows have this contamination**.

**This explains the universal ~68% plateau across every architecture we tried** (TF-IDF, MiniLM, BGE, FinBERT, ensembles, RAC). It wasn't an encoder problem. It was a data-preparation problem.

---

## 3. Week 5 objectives

1. **Validate the LongProfile-contamination hypothesis.** If segment-only inputs unlock 73%+ Macro F1, our diagnosis is correct.
2. **Layer hierarchy-aware modeling** (multi-task heads for sector → group → industry) on top of clean inputs.
3. **Apply long-tail losses** (Distribution-Balanced loss or Dynamic Class Average Loss) to lift rare-class F1.
4. **Add retrieval augmentation** for tail codes (the 50+ classes with fewer than 200 training samples).
5. **Hit ≥ 75% Macro F1** on Task 1 as the team's contract deliverable. Stretch: 80%.
6. **Begin Task 2** (450 business activity codes) using the same architecture, exploiting the deterministic Task-1 → Task-2 mapping as a hard constraint.

---

## 4. Task assignments

Pick or shuffle these by team strengths. Each lane has a clear deliverable.

### Lane A — Input cleanup + baseline validation (Owner: __________)

**Goal:** Prove or disprove the LongProfile contamination hypothesis.

- [ ] Fork `scripts/train_cascade_v5_hybrid.py`. Create `scripts/v18_segment_only.py`.
- [ ] In the new script, replace the text input with **SegmentName + ". " + SegmentDescription only** (drop LongProfile entirely).
- [ ] Keep the rest of the V5 stack identical: TF-IDF + MiniLM + BGE + numerical features.
- [ ] Train LinearSVC (C=1.0, class_weight='balanced').
- [ ] Report Macro F1, accuracy, top-10 pass on `task1_test.csv`.
- [ ] If Macro F1 ≥ 73%, mark hypothesis confirmed and notify Lane B/C immediately.
- [ ] Also run a variant where LongProfile is included **with a weight of 0.3** vs SegmentDescription at 1.0 (downweighted, not removed).

**Deliverable:** `models_v18/training_summary.json` + 1-paragraph writeup of result.

**Estimated time:** 2 hours (uses cached embeddings).

---

### Lane B — Hierarchy-aware DeBERTa multi-task head (Owner: __________)

**Goal:** Train a single encoder that predicts sector, group, AND industry jointly, with hierarchy-consistent loss.

- [ ] Build a Colab notebook (`colab/deberta_hierarchical.ipynb`).
- [ ] Use `microsoft/deberta-v3-base` as the encoder.
- [ ] Input: **SegmentName + SegmentDescription only** (per Lane A finding).
- [ ] Three classification heads:
  - Sector head (11 classes)
  - Group head (55 classes)
  - Industry head (145 classes)
- [ ] Joint loss = α·CE(sector) + β·CE(group) + γ·CE(industry), with α=0.2, β=0.3, γ=0.5.
- [ ] Train 5 epochs, batch 32, learning rate 2e-5, AdamW, linear warmup 10%.
- [ ] At inference: use industry head argmax. Report Macro F1 + top-10 pass.
- [ ] Also save the model's [CLS] embeddings for stacking.

**Deliverable:** `models_v19/` with model weights + embeddings + summary JSON.

**Estimated time:** 4-6 hours (Colab T4: 30 min/epoch × 5 = 2.5 hr training + 1 hr setup/eval).

---

### Lane C — Long-tail loss + class-balanced sampling (Owner: __________)

**Goal:** Improve macro-F1 specifically on the rare classes (the bottom 50 of 145 codes).

- [ ] Read the [Balancing Methods for Multi-label Text Classification with Long-tailed Class Distribution paper](https://aclanthology.org/2021.findings-acl.165/) — focus on the **Distribution-Balanced (DB) loss** section.
- [ ] Modify Lane B's training script to swap CrossEntropyLoss for DB loss.
- [ ] Implement class-balanced mini-batch sampler (each batch contains a mix of head and tail codes).
- [ ] Compare Macro F1 on the 50 rarest classes before vs after.
- [ ] Document per-class F1 lift in a table.

**Deliverable:** `WEEK_5_LONG_TAIL_ANALYSIS.md` with per-class F1 deltas.

**Estimated time:** 6 hours.

---

### Lane D — Retrieval-augmented classification (Owner: __________)

**Goal:** Boost tail-class F1 by retrieving K nearest training neighbors and using them as additional context.

- [ ] Build a FAISS index over Lane B's training embeddings.
- [ ] For each test sample, retrieve top-20 nearest training samples.
- [ ] At classification time, take a **majority vote** over neighbor labels and combine with Lane B's classifier prediction via:
  - 70% weight: classifier prediction
  - 30% weight: KNN vote
- [ ] Compare Macro F1 vs Lane B alone.

**Deliverable:** `models_v20/training_summary.json` + the FAISS index file.

**Estimated time:** 4 hours.

---

### Lane E — Task 2 scaffolding (Owner: __________)

**Goal:** Get Task 2 (450 business activity codes) infrastructure ready while Lanes A-D iterate on Task 1.

- [ ] Load Task 2 data from `data/raw/`.
- [ ] Build the **deterministic Task 1 → Task 2 mapping** (which subindustry codes belong to which industry?). Verify it's truly one-to-many as the case states.
- [ ] Build a per-industry subindustry classifier: given the predicted Task 1 code, restrict Task 2 predictions to that industry's subset of subindustries.
- [ ] Reuse Lane B's encoder + features (no new encoding required).

**Deliverable:** `WEEK_5_TASK2_SCAFFOLD.md` with mapping verification + initial baseline.

**Estimated time:** 5 hours.

---

### Lane F — Demo + documentation (Owner: __________)

**Goal:** Update the demo server with the winning model and rewrite confidence display honestly.

- [ ] Replace `server_legendary.py`'s cascade predictor with whichever Week 5 model wins.
- [ ] Replace the fake `softmax(svm_margin)` confidence with **calibrated probabilities** from CalibratedClassifierCV.
- [ ] Add a "top-3 predictions" panel showing alternative interpretations for low-confidence inputs.
- [ ] Test demo on 10 hand-typed inputs spanning easy + ambiguous cases.
- [ ] Update `CASCADE_AUDIT.md` with Week 5 results.

**Deliverable:** Working demo on port 5003 + 1-page screenshot writeup.

**Estimated time:** 4 hours.

---

## 5. Decision points + ordering

```
Lane A (segment-only baseline)
    ↓ result by Tue EOD
    ├── If ≥ 73%: confirmed input cleanup is the lever
    │      → Lanes B/C/D all use SegmentName + SegmentDescription only
    └── If < 70%: contamination wasn't the cause
           → Lane B uses concatenated text (current input)
           → Lane C/D priority increases

Lane B (hierarchical DeBERTa) — runs Wed-Thu
    ↓ result by Thu EOD
Lane C (long-tail loss) — runs Thu-Fri (builds on Lane B)
Lane D (retrieval augmentation) — runs Fri (builds on Lane B)
Lane E (Task 2) — runs in parallel Tue-Sat (no dependencies)
Lane F (demo) — runs Sat (after model is chosen)
```

---

## 6. Definition of done — Week 5

Sprint is successful if by Saturday night we have:

- [ ] Lane A result: ≥ 73% Macro F1 on segment-only inputs, OR documented evidence the hypothesis is wrong.
- [ ] Lane B result: hierarchical DeBERTa model trained and evaluated.
- [ ] At least one Lane C/D experiment showing lift over Lane B.
- [ ] Lane E: Task 2 baseline ≥ 50% Macro F1.
- [ ] Lane F: working demo with honest confidence display.
- [ ] All models reproducible: training scripts committed, model artifacts saved, summary JSONs written.

Stretch goal: **Task 1 Macro F1 ≥ 75% on `task1_test.csv`.**

---

## 7. What we are NOT doing this week

- No more flat 145-class classifiers without hierarchy awareness.
- No more concatenated LongProfile + Segment inputs (pending Lane A verification).
- No more cascade-style top-down inference (V2/V3 style) — moving to joint hierarchical heads instead.
- No FinBERT (tried, underperformed — financial NEWS domain ≠ company segment descriptions).
- No cloud inference APIs at demo time. Training on Colab is fine; demo runs locally.

---

## 8. Communication

- Daily standup: 15 min, 9 AM CDT. Each lane reports yesterday's progress + today's blocker.
- Slack channel: `#mgt599-week5` (or wherever the team uses).
- Anyone hitting a 2+ hour blocker → post in channel immediately. Don't burn a day stuck.
- Friday 5 PM: dry-run of Saturday's results presentation.

---

## 9. References — papers the team should skim

- [Balancing Methods for Multi-label Text Classification with Long-tailed Class Distribution](https://aclanthology.org/2021.findings-acl.165/) — DB loss
- [HiAGM: Hierarchy-Aware Global Model for Hierarchical Text Classification](https://aclanthology.org/2020.acl-main.104/) — hierarchical label graphs
- [Hierarchical Text Classification: Survey 2024](https://www.mdpi.com/2079-9292/13/7/1199) — survey of recent methods
- [Retrieval-augmented Multi-label Text Classification (Chalkidis & Kementchedjhieva)](https://arxiv.org/abs/2305.13058) — retrieval for tail labels
- [DeBERTa-v3 paper](https://arxiv.org/abs/2111.09543) — encoder of choice for Lane B

---

*Prepared: 2026-05-10. Sprint review: 2026-05-16 18:00 CDT.*
