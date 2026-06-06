---
title: GECS Sage Classifier
emoji: 🏭
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
---

# GECS-Sage Classifier

MGT 599 Capstone, Group 4, DePaul University Chicago.

GECS-Sage classifies company or segment text into Morningstar GECS industry and sub-industry codes. The Space runs the cascade demo path and presents Task 1 industry routing plus constrained Task 2 sub-industry prediction.

## Model Card

- Task 1: audited cascade baseline over 145 GECS industry classes.
- Task 2: constrained 428-class sub-industry cascade, 55.44% Macro F1.
- Taxonomy grounding: GECS labels and definitions from `gecs_taxonomy.json`.
- Audit note: the historical 88.90% Task 1 result was leakage-contaminated and is not the shipped performance claim.

## Setup

Copy the model files from the GitHub repo into this Space's `models/` directory:

- `models/cascade_vectorizer.pkl`
- `models/cascade_L1_svm.joblib`
- `models/cascade_L2_models.joblib`
- `models/cascade_L3_models.joblib`
- `models/t2_cascade_seg_vec.pkl`
- `models/t2_cascade_L4_seg.joblib`
- `models/sub_industry_labels.json`
- `models/mstar_labels_full.json`

For the newer constrained Task 2 build, copy `models_task2/t2_cascade_L4_seg.joblib`, `models_task2/t2_cascade_seg_vec.pkl`, and `models_task2/task1_to_task2_map.json` into the matching Space asset path used by the app.
