# Week 3: Model Architecture and Pipeline Design

This document details the end-to-end model development strategy, architecture choices, training procedures, and deployment pipeline for the Core Classification ML tasks (Task 1 & Task 2) for Group 4's Capstone. 

Importantly, this ecosystem heavily integrates **`breezeml`**, our custom built machine learning library, to demonstrate advanced software engineering and robust model orchestration.

---

## 1. Objective and Model Definitions

The project involves two primary natural language processing (NLP) classification tasks using `SegmentDescription` definitions to assign structural codes:

1. **Task 1: Global Industry Assignment (MstarGlobal)**
   - **Target:** High-level macroscopic industry labels.
   - **Model:** TF-IDF representation paired with a robust classification head (Logistic Regression or Random Forest).
2. **Task 2: Business Activity Assignment (Subindustry)**
   - **Target:** Granular 10-digit microscopic subindustry codes.
   - **Model:** Deep TF-IDF layered with XGBoost/SVM, utilizing SMOTE due to severe class imbalance.

---

## 2. Model Architecture Choices

We deliberately avoided massive deep learning models (like BERT or GPT embeddings) in favor of Classical NLP approaches, orchestrated by our custom `breezeml` toolkit. 

### Why TF-IDF and Classical ML?
1. **Computational Efficiency:** Our data is characterized by massive class imbalances but relatively short text descriptions. TF-IDF processes 50,000+ short descriptions in seconds natively.
2. **Interpretability:** In financial analysis, the ability to trace an industry classification back to a specific feature (like the term "saas" or "brokerage") is critical. TF-IDF and tree-based coefficients offer perfect traceability.
3. **`breezeml` Integration:** Leveraging our proprietary `breezeml` library allows us to build highly customized, reproducible training pipelines without the bloat of relying purely on generalized third-party monolithic frameworks.

---

## 3. Training Procedures

The end-to-end training cycle utilizes a strict isolation procedure to prevent data leakage.

1. **Data Ingestion & Preprocessing:** 
   - `task1_clean.csv` and `task2_clean.csv` are loaded.
   - Missing values in `SegmentDescription` are handled by `breezeml.preprocessing` pipelines.
2. **Data Splitting:** 
   - An 80/20 train/test split utilizing a stratified approach to assure that all rare "orphan" subindustries are represented in both sets.
3. **Addressing Class Imbalance (Task 2 specifically):**
   - We observed massive gravitational "super-hubs" in our Week 2 graph (some subindustries having 5,000 instances, others having <10). 
   - SMOTE (Synthetic Minority Over-sampling Technique) is applied strictly on the *training set* prior to feature vectorization to inflate the minority decision boundaries.
4. **Vectorization & Fit:**
   - Text is fit via a TF-IDF vectorizer limited to the top 5,000 most predictive unigram/bigram features.
   - Classifier is trained using hyperparameter grid-search cross-validation (CV=5).

---

## 4. Retraining Strategy (Handling Concept Drift)

In business environments, the taxonomy of activities constantly evolves (e.g., "AI", "Cloud", and "Blockchain" were virtually non-existent concepts 15 years ago but are dominant sectors today).

**Drift Detection:**
- We monitor the macro F1-score on newly ingested ground-truth segments quarterly.
- If the F1-score drops beneath our 0.85 tolerance threshold, a flag is thrown via the `breezeml.drift_monitor` module.

**Automated Retraining:**
1. A cron job invokes a retraining pipeline utilizing a rolling 5-year window of the newest data.
2. The TF-IDF vocabulary is refit to establish new dominant unigrams/bigrams.
3. The newly champion-modeled artifacts (`.pkl`) are promoted to the active registry automatically if cross-validation scores prove superior to the current active model.

---

## 5. End-to-End Solution Pipeline (Production Integration)

To support reproducibility, we move away from static notebooks for the final product and utilize a modular CI/CD methodology.

* **Layer 1: Data Lake.** Cleaned CSVs are stored securely.
* **Layer 2: Training Engine.** `train_pipeline.py` executes the `breezeml` training wrapper, creating the TF-IDF and Model `.pkl` elements.
* **Layer 3: Artifact Registry.** The `breezeml.registry` tracks model versions, logging hyperparameters seamlessly.
* **Layer 4: Inference API.** The final models are hosted via a lightweight FastAPI or Flask wrapper. An incoming REST payload containing a `SegmentDescription` hits the API, runs through the cached TF-IDF vectorizer natively, and returns the Predicted Task 1 and Task 2 JSON array instantly.
