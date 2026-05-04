---
title: GECS Cascade Classifier
emoji: 🏭
colorFrom: blue
colorTo: indigo
sdk: gradio
sdk_version: 4.36.1
app_file: app.py
pinned: false
python_version: "3.11"
---

# GECS Hybrid Cascade Industry Classifier

**MGT 599 Capstone · Group 4 · DePaul University Chicago**

4-level LinearSVC cascade for Morningstar GECS industry and sub-industry classification.

- **Task 1**: Sector -> Group -> MSTAR code — **88.90% Macro F1**, 145 classes
- **Task 2**: T1 cascade + L4 sub-industry — **55.41% Macro F1**, 428 classes (+19pp over DeBERTa)
- **Architecture**: TF-IDF (60K features) + LinearSVC at each level
- **Training time**: ~3 minutes vs 3+ hours for DeBERTa

## Setup

Copy the following model files from the GitHub repo into the `models/` directory:
- `models/cascade_vectorizer.pkl`
- `models/cascade_L1_svm.joblib`
- `models/cascade_L2_models.joblib`
- `models/cascade_L3_models.joblib`
- `models/t2_cascade_seg_vec.pkl`
- `models/t2_cascade_L4_seg.joblib`
- `models/sub_industry_labels.json`
- `models/mstar_labels_full.json`
