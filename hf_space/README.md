---
title: GECS DeBERTa Classifier
emoji: 🏭
colorFrom: red
colorTo: black
sdk: gradio
sdk_version: 4.36.1
app_file: app.py
pinned: false
---

# GECS DeBERTa-v3 Industry Classifier

**MGT 599 Capstone · Group 4 · DePaul University Chicago**

Fine-tuned `DeBERTa-v3-small` for Morningstar GECS Task 1 industry classification across 29 well-represented classes.

- **Model**: `microsoft/deberta-v3-small` (141M params)
- **Task**: Classify corporate descriptions into GECS industry codes
- **Macro F1**: 78.10% on Certified Operational Scope (29 classes)
