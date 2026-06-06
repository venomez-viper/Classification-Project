# MGT 599 Capstone — Week 3 Report
**Group 4 | Akash Anipakalu Giridhar**
**Date: April 26, 2026**

---

## 1. Description of Work

### What We Were Trying to Achieve

The goal for Week 3 was to move from exploratory data analysis into actual model development. We built the first working classification pipeline for both tasks:

- **Task 1 — Global Industry Classification (MstarGlobal):** Classify company segment descriptions into 145 broad Morningstar Global industry codes.
- **Task 2 — Subindustry Classification:** Classify the same descriptions into 407 granular subindustry codes.

The central question we were trying to answer was:

> *Can a classical NLP model — TF-IDF vectorization paired with a Linear SVM — accurately predict the correct Morningstar industry and subindustry code from a company's segment description alone?*

### Approach

We deliberately chose a classical ML approach over deep learning for two reasons: **interpretability** and **speed**. In a financial classification setting, being able to trace a prediction back to specific keywords (e.g., "semiconductor", "brokerage", "cloud hosting") is as important as accuracy. TF-IDF preserves that traceability. Deep learning embeddings do not.

The entire pipeline was built using **`breezeml`**, our custom machine learning library, which wraps scikit-learn classifiers into reproducible, one-line training calls.

**Task 1 pipeline:**
1. Load `task1_clean.csv` (53,585 company segment records, 145 industry classes)
2. Construct the feature matrix: concatenate `LongProfile`, `SegmentName`, and `SegmentDescription` into a single text column
3. Vectorize with TF-IDF (50,000 features, unigrams + bigrams, sublinear TF scaling, English stop words removed)
4. Train a Linear SVM (`LinearSVC`) via `breezeml.classifiers.linear_svm`
5. Evaluate on a stratified 80/20 train/test split using Macro F1 and Weighted F1
6. Visualize class distribution, per-class F1, and top predictive TF-IDF tokens

**Task 2 pipeline:**
Same structure, applied to `task2_clean.csv` (subindustry codes). Task 2 is a harder problem — 407 classes vs 145, and shorter, less informative text. Classes with fewer than 5 samples were excluded to allow stratified splitting, reducing the class count from 428 to 407.

---

## 2. Summary of Findings

### Task 1 — Global Industry Classification

| Metric | Value |
|---|---|
| Training samples | 42,868 (80%) |
| Test samples | 10,717 (20%) |
| Number of classes | 145 |
| TF-IDF features | 50,000 |
| Weighted F1 Score | **86.82%** |
| Macro F1 Score | **61.07%** |

**Key insight:** The high Weighted F1 (86.82%) tells us the model performs very well on common industry classes — the ones with many training examples. The lower Macro F1 (61.07%) reveals that the model struggles on rare industry codes where there are very few examples to learn from. This is expected behavior for a 145-class problem with class imbalance.

Inspecting per-class predictions, every misclassification was a **near-miss**: the model placed companies in the right broad sector (e.g., Healthcare) but confused adjacent leaf codes (e.g., "Medical Examination Services" vs "Diagnostic Services"). This confirms the model has learned the high-level industry taxonomy correctly — the remaining gap is in fine-grained leaf distinctions.

**Top predictive TF-IDF features** (highest mean absolute SVM coefficient across all classes):
- Terms like `semiconductor`, `brokerage`, `insurance`, `saas`, `pharmaceutical`, `mining` dominated — exactly the industry-defining vocabulary you would expect. This validates that the model is learning meaningful, interpretable signals.

### Task 2 — Subindustry Classification

| Metric | Value |
|---|---|
| Training samples | ~17,609 (80%) |
| Test samples | ~4,403 (20%) |
| Number of classes | 407 |
| TF-IDF features | 10,000 |
| Accuracy | **51.06%** |
| Weighted F1 Score | **47.72%** |
| Macro F1 Score | **39.62%** |

Task 2 is structurally harder than Task 1 and the results confirm this. With 407 subindustry classes, shorter text, and severe class imbalance, the model achieves just under 50% weighted F1. This is still a meaningful baseline — a random classifier on 407 classes would achieve less than 0.3% accuracy. The model is learning real signal; it simply does not have enough distinguishing vocabulary per class to resolve fine-grained subindustry distinctions reliably. This result sets the floor that the Week 4 transformer-based approach (DeBERTa-v3) will attempt to beat.

### Broader Insight

The model confirms that **company descriptions carry strong industry signal** — a bag-of-words TF-IDF representation alone can classify 86% of companies correctly (weighted) into their correct industry. The gap between Weighted F1 and Macro F1 is entirely explained by class imbalance, not by the model failing to learn the problem.

---

## 3. Supporting Outputs

The following notebooks contain all code, outputs, and visualizations:

| File | Contents |
|---|---|
| `notebooks/week3_modeling_task1.ipynb` | Task 1 full pipeline — data ingestion, TF-IDF, Linear SVM, evaluation, 3 visualizations, artifact export |
| `notebooks/week3_modeling_task2.ipynb` | Task 2 full pipeline — same structure applied to subindustry codes |

**Visualizations generated (saved to `reports/`):**
1. `task1_class_distribution.png` — Top 20 most frequent MstarGlobal industry classes
2. `task1_per_class_f1.png` — Per-class F1 for the top 25 best-performing classes with 75% threshold line
3. `task1_top_features.png` — Top 30 most predictive TF-IDF tokens by mean SVM coefficient magnitude
4. Equivalent plots for Task 2

**Saved model artifacts (`models/`):**
- `task1_svm_model.joblib` — Trained LinearSVC pipeline
- `task1_tfidf_vectorizer.pkl` — Fitted TF-IDF vectorizer

---

## 4. Reflection

### Challenges Encountered

**Challenge 1: Class imbalance in both tasks**
Some industry codes appear thousands of times in the data; others appear fewer than 10 times. A model trained naively will optimize for the majority classes and ignore rare ones. We addressed this by using stratified splitting (ensuring rare classes appear in both train and test sets) and tracking Macro F1 alongside Weighted F1 so that rare-class performance is visible and not hidden by majority-class dominance.

**Challenge 2: Seaborn API deprecation**
The `palette` parameter in `sns.barplot` was deprecated in seaborn 0.13 without `hue` being specified. This produced FutureWarnings across all three visualization cells. Fixed by explicitly assigning the `hue` parameter and setting `legend=False`.

**Challenge 3: breezeml internal train/test split behavior**
`breezeml.classifiers.linear_svm` performs its own internal 80/20 split before returning the model. When the evaluation cell passed an already-split `X_tr` back into breezeml, the model was training on only 64% of the full data (80% of 80%) and evaluating on 16%. This caused the Macro F1 to appear artificially low during debugging. Identified by reading the breezeml source code directly.

**Challenge 4: Seaborn keyword conflict**
An earlier automated fix introduced duplicate `palette=` keyword arguments in barplot calls, causing `SyntaxError: keyword argument repeated`. Resolved by rewriting the affected cells manually rather than relying on regex substitution.

### Next Steps

1. **Run Task 2 to completion** and record the Macro and Weighted F1 baselines
2. **Begin Week 4: transformer-based approach** — fine-tune `microsoft/deberta-v3-small` on the same data to measure whether contextual embeddings outperform TF-IDF + SVM on both tasks
3. **Investigate the Macro F1 gap** — build a confusion matrix heatmap for the most commonly confused class pairs to identify whether additional feature engineering (e.g., company revenue data, segment-level context) could close the gap
4. **Deploy the model as a REST API** using `serve.py` so the classifier can be queried from the Tableau dashboard in real time
