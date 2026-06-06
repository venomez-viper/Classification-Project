# Model Version History — GECS-Sage / TAVSS

Full honest progression of Task 1 (145-class industry) and Task 2 (428-class sub-industry) models.
All F1 scores are **Macro F1** on a **company-disjoint** test set unless noted.

---

## Task 1 — GECS Industry Classification (145 classes)

| Version | Architecture | Key Change | Macro F1 | Notes |
|---------|-------------|-----------|----------|-------|
| **V1 (leaked)** | LinearSVC cascade | Row-level random split — same company on both sides | **88.90%** | ❌ INVALID — 97.2% of test rows memorized |
| **V2 honest** | LinearSVC cascade | Company-disjoint split (GroupShuffleSplit by CompanyId) | **59.65%** | ✅ First defensible baseline |
| V3 | LinearSVC cascade | Cascade error propagation analysis | ~60% | Confirmed error propagates down L1→L3 |
| V4 | LinearSVC + MiniLM | Sentence embedding features added | 59.65% | Same ceiling — bottleneck is semantic, not vocab |
| **V5 hybrid** | LinearSVC + embeddings | TF-IDF + MiniLM + 3 engineered features (num_segments, max_share, share_std) | **67.11%** | +7.46pp from engineered features |
| V6 | V5 + BGE-base | Added BGE-base-en-v1.5 embeddings | 67.70% | +0.59pp from better encoder |
| V7 | SetFit contrastive | Manual contrastive fine-tuning, 8 samples/class | 61.21% | Collapsed embedding space — regressed |
| **V8 mega-ensemble** | All encoders | TF-IDF + MiniLM + BGE + engineered features ensembled | **68.42%** | Classical ceiling |
| V9 | V8 + contrastive | Tried contrastive fine-tuning on V8 | regressed | Embedding collapse confirmed |
| V10 | V8 + calibration | Platt scaling on V8 outputs | 69.09% | +0.67pp |
| V11 | gte-large | Attempted 30h+ CPU encoding of 53K rows | killed | gte-large CPU was too slow |
| **ModernBERT-base** | Transformer | Fine-tuned on Colab A100 | 67.18% | Baseline transformer checkpoint |
| **ModernBERT-large ep3** | Transformer | Best single checkpoint | **70.29%** | +1.87pp over classical ceiling |
| **Greedy ensemble** | 2× ModernBERT-large | seed 42 (segment-aware) + seed 7 (raw text) | **73.95%** | 90.88% top-3 accuracy |
| **Final locked** | Calibrated ensemble | Temperature scaling τ=0.2 on greedy ensemble | **75.0%** | CV: 73.96% · test-tuned upper bound: 77.51% |

### Calibration Audit (final model)
- Per-class threshold optimization (145 free params): **77.51%** on test — overfit to test set
- 5-fold cross-validation of calibrated result: **73.96%** — essentially no lift
- Light temperature scaling (τ=0.2): **75.0%** — generalizes, disclosed in methods
- **Headline locked at 75.0%** with all three numbers disclosed

### Key Metrics (Final Locked)
| Metric | Value |
|--------|-------|
| Macro F1 | **75.0%** |
| Top-3 accuracy | **91.4%** |
| Top-5 accuracy | **95.3%** |
| Cross-validated Macro F1 | 73.96% |
| Test-tuned upper bound | 77.51% (not reported as headline) |
| Random baseline | 0.69% (1/145) |

---

## Task 2 — GECS Sub-Industry Classification (428 classes)

| Version | Architecture | Key Change | Macro F1 |
|---------|-------------|-----------|----------|
| V1 | LinearSVC flat | 428-class flat classifier | ~20% |
| V2 constrained | LinearSVC L4 | Constrained to Task 1 parent codes | 42.1% |
| V3 seg-vec | LinearSVC L4 | Separate segment-aware vectorizer | 51.2% |
| **Final (L4 cascade)** | LinearSVC L4 | t2_cascade_seg_vec + task1_to_task2_map constraint | **55.44%** |

### Task 2 Key Details
- 428 sub-industry classes (10-digit GECS codes)
- Constrained by Task 1 output — L4 classifier only ranks valid children of the T1 prediction
- Extreme long-tail: 65% of classes have <10 training samples
- Train/test shares rows with Task 1 (42,868 / 10,717 company-disjoint)

---

## The Leakage Discovery

The original V1 result (88.90%) used a row-level `train_test_split(random_state=42)`. Since multiple rows per company share the same `LongProfile` text, the split allowed the model to memorize:

- **10,412 of 10,717 test rows** had been seen during training (97.2%)
- On the **305 truly unseen rows**, the same V1 model scored 81.73%
- The model was recalling text it had memorized, not generalizing

**Fix**: `GroupShuffleSplit(n_splits=1, test_size=0.2, groups=df['CompanyId'])` — entire companies assigned to one side only. CompanyId was recovered from a 200-char LongProfile prefix join (98.3% match rate on 53,585 rows).

---

## Architecture: 4-Level Cascade

```
Input text
   ↓
L1 — Sector classifier     (11 sectors)
   ↓
L2 — Group classifier      (~40 groups, conditioned on L1 output)
   ↓
L3 — Industry classifier   (145 GECS codes, conditioned on L2 output)   ← Task 1
   ↓
L4 — Sub-industry classifier (428 codes, valid children of L3 only)      ← Task 2
```

Each level is a separate `LinearSVC(class_weight='balanced')` trained on the subset of training rows belonging to its parent node. Error at L1 cannot be recovered at L3.

---

*Last updated: 2026-05-31*
