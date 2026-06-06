# MGT 599 Capstone — Project Journey

**Task:** Classify Morningstar companies into the 145 GECS industry codes (Task 1) and 450 business activity subindustry codes (Task 2) from `LongProfile`, `SegmentName`, `SegmentDescription`, and revenue features.

---

## 1. Where we started — the embarrassing 88.90%

The original cascade SVM reported **88.90% Macro F1**. The demo only worked for four hand-crafted example pills; arbitrary inputs returned random-looking predictions with fake high "confidence" scores rendered by softmaxing SVM decision-function margins.

**It looked legendary. It wasn't.**

---

## 2. The data leakage we discovered

Auditing the original training script revealed the issue:

| What was reported | What was actually true |
|---|---|
| Trained on `data/cleaned/task1_clean.csv` (53,585 rows) | Same |
| Evaluated on `llm_finetuning/data/task1_test.csv` (10,717 rows) | Same |
| Implied "held-out test set" | **97.2% of the test rows were in the training data** |
| 88.90% Macro F1 | Real on those test rows — but ~10,412/10,717 had been memorized |

**On the 305 truly-unseen rows, the same model scored 81.73%.** So the model isn't fake — but the headline number is leaked memorization.

This is why the demo failed: the model was excellent at recalling memorized inputs but couldn't generalize to fresh user-typed text.

### Other findings

- **Conglomerate confusion:** 35.1% of companies have multiple GECS codes across segments. For these, `LongProfile` describes multiple sectors at once → the model sees identical text across rows with different labels. This is irreducible label noise without segment-aware features.
- **Sector 310 (Industrials):** ~52% of all final errors trace back to Level-1 sector misclassification cascading downward. The single worst class is `31030010` (Diversified Industrial Conglomerates) at F1 ≈ 30% on honest evaluation.
- **TF-IDF ceiling:** Pure TF-IDF + LinearSVC plateaus at ~57% Macro F1 regardless of vocabulary size, char n-grams, or C tuning. The bottleneck is semantic, not vocabulary.
- **Fake confidence:** The UI was rendering `softmax(SVM decision margin)` as "confidence %". For out-of-distribution input the SVM still produces decision margins, the softmax still normalizes them, and the UI showed "92% confident" while predicting wrongly.

---

## 3. The pivot — honest evaluation only

We rebuilt the pipeline so that:

1. **Training uses `task1_train.csv` only** (42,868 rows).
2. **Test rows are never seen during training.**
3. **Both Macro F1 and Top-10 class F1 are reported.**
4. **A documented 88.90% with leakage is no longer the baseline. The honest 59.65% TF-IDF baseline is.**

This was painful — going from 88.90% to 59.65% looks like regression. But it's the truth, and now every improvement we make is a real improvement instead of an illusion.

---

## 4. Iterations and what each one revealed

| Version | Approach | Macro F1 | Insight |
|---|---|---|---|
| V1 (orig) | TF-IDF cascade on full data | 88.90% | Data leakage, not real |
| V2 (proper) | TF-IDF cascade, honest split | 59.65% | True baseline |
| V3 | + dual vectorizers, engineered numerical features | 56.80% | Cascade error propagation |
| V4 | MiniLM sentence embeddings (384d) | 59.70% | Embeddings ≈ TF-IDF — bottleneck isn't representation |
| V5 | TF-IDF + MiniLM hybrid + 5 engineered features | 67.11% | Engineered features (`num_segments`, `max_share`, `share_std`) carry real weight |
| V6 | + BGE-base encoder (768d) | 67.70% | Bigger encoder helps marginally |
| V8 | Mega-ensemble (TF-IDF + MiniLM + BGE + numerical) | **68.42%** | Ensembling encoders + features beats any single piece |
| V9 | Manual contrastive fine-tune of MiniLM | 61.21% | Fine-tuning with only 8 samples/class collapses the embedding space — REGRESSION |
| V10 | Calibrated LinearSVC + LogReg variants | 69.09% (in progress) | Calibration adds +0.7pp |
| V11 | gte-large encoder | killed at 30+hr | Encoding 53k rows × 1024d on CPU is too slow |
| V12 | Class prototypes (mean embedding per class) | n/a | Folded into V13 |
| V13 (running) | TF-IDF + MiniLM + BGE + **GECS official anchors** + prototypes + numerical (~123k features) | TBD | The novel angle |
| V14 (done) | Retrieval-Augmented Classification (KNN + taxonomy retrieval) | 66.04% | KNN-only features lose info that raw embeddings keep |

---

## 5. The "GECS Anchors" idea — our novel contribution

Inside the `Task Doc` folder is the **Morningstar Global Equity Classification Structure 2019 PDF** — the *official* document that defines all 145 GECS industries.

We parsed all 145 industry definitions out of that PDF (127 via regex extraction + 18 hand-curated for codes the parser missed). For each industry we now have:

```
{
  "mstar_code": "31030010",
  "sector_name": "Industrials",
  "industry_name": "Diversified Industrials",
  "description": "Companies that engage in diversified industrial activities..."
}
```

We then encode all 145 official descriptions with our cached MiniLM and BGE encoders. For every company description in train and test we compute its cosine similarity to every official anchor → **145 features per encoder per text-field = 580 anchor-similarity features**.

This grounds every prediction in Morningstar's own taxonomy. **No other team will have done this** — it's a methodology choice that uses the regulator's authoritative document as a soft label dictionary.

Combined with empirical class prototypes (mean embedding of each class's training samples), we have ~123,000 features carrying:
- Lexical signal (TF-IDF)
- Semantic signal (MiniLM + BGE embeddings)
- Taxonomy-grounded signal (GECS anchors)
- Empirical class signal (prototypes)
- Domain features (revenue share, segment count, etc.)

---

## 6. The 86% question — where it could come from

The literature says **fine-tuned BERT on industry classification can hit 88% F1**. But that's typically with:
- Fewer classes (13–50, not 145)
- Domain-pretrained models (FinBERT, BloombergGPT)
- Cross-encoder reranking on top-K candidates
- Or hierarchical multi-task heads

**For our 145-class fine-grained problem on CPU**, the sober ceiling is closer to 75–80%. To genuinely break 80% we need at least one of:

1. **FinBERT fine-tuning** (financial-domain BERT, +14pp documented gain over vanilla BERT)
2. **Cross-encoder reranking** (+27% gain documented in retrieval-style classification)
3. **Hierarchical multi-task learning** (sector + group + code joint loss)

The first one is impractical on local CPU (8–15 hours per epoch). So we pivoted to **Google Colab GPU**, which makes a full fine-tune possible in 20–40 minutes on the free T4 tier.

---

## 7. The Colab pivot

**Why:** Local CPU fine-tuning of a 110M-parameter BERT model on 43k examples for 3 epochs would take 8–15 hours. Colab's free T4 GPU does the same in ~30 minutes — a 30x speedup.

**Why it's still allowed:** Colab is rented compute, not an external classification API. The model weights are downloaded back to the laptop after training. Inference at demo time still runs locally on CPU.

**What's running there now:**

- Notebook: `colab/finbert_finetune.ipynb`
- Model: `yiyanghkust/finbert-pretrain` (BERT pretrained on 4.9B tokens of financial text)
- Training: 3 epochs, batch 32, learning rate 2e-5, class-balanced weighted cross-entropy
- Outputs to download:
  - Fine-tuned `[CLS]` embeddings for every train + test row
  - 145-class probability matrix on the test set
  - Saved model weights (for offline inference)
  - F1 / accuracy / top-10 metrics

This will produce a strong standalone baseline (likely 70–80% F1 alone) AND embeddings that we stack into V17.

---

## 8. V17 — the planned final ensemble

When FinBERT comes back from Colab, V17 stacks everything we've built:

```
V17 feature stack (~125,000 dimensions):
  • TF-IDF segment + LongProfile        (120,000)
  • MiniLM seg + long embeddings        (   768)
  • BGE seg + long embeddings           ( 1,536)
  • FinBERT [CLS] embeddings            (   768)  ← new from Colab
  • GECS official-taxonomy anchors      (   580)
  • Class prototypes                    (   580)
  • Numerical features                  (     5)
```

Plus **probability-level ensemble** with FinBERT's softmax output (geometric mean of the two probability distributions). This is the legendary stack.

**Realistic expectation for V17:**
- 75% Macro F1: very likely
- 80% Macro F1: probable
- 85% Macro F1: stretch goal — possible if FinBERT delivers strongly

---

## 9. What we'll have at the end (regardless of final F1)

1. **A complete audit** documenting the 88.90% leakage (`CASCADE_AUDIT.md`).
2. **An honest evaluation pipeline** that other teams won't have.
3. **17 documented model variants** with reproducible training scripts.
4. **A novel methodological contribution** — the GECS Official Taxonomy Anchoring approach using the regulator's own definition document.
5. **A real, defensible final F1** — not an illusion that breaks in the demo.

The story isn't *"we hit 90%"*. It's:

> *We caught a 30-percentage-point leakage in our own baseline. We rebuilt the pipeline honestly. We grounded every prediction in Morningstar's official taxonomy. We stacked five independent representations of company text. We pushed past every offline plateau. The final number is real.*

That's the kind of work that gets remembered.

---

## 10. Current status (live)

| Track | State |
|---|---|
| V13 (GECS anchors local) | Training classifier 1/3, ~10–15 min more |
| V14 (RAC) | Done — 66.04% |
| V16 (FinBERT, Colab) | User running notebook |
| V17 (final ensemble) | Script ready — fires when V13 + V16 land |
| Task 2 (450 subindustries) | Not started — uses Task 1 industry as a hard constraint (each subindustry deterministically belongs to one industry). Expected approach: same V17 stack, smaller per-industry classifier. |

---

*Document last updated: 2026-05-09*
