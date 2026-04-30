# LLM Fine-Tuning: GECS Classification

> **Scope:** This is a standalone research project investigating whether a small fine-tuned LLM
> can outperform the TF-IDF + Linear SVM baseline on Morningstar GECS classification.
> It is **completely independent** of the main capstone pipeline, Flask API, and frontend.

---

## Project Goal

Fine-tune a small pretrained transformer (DeBERTa-v3-small or similar) on company descriptions
to predict two targets:

- **Task 1:** 145 Morningstar industry codes
- **Task 2:** 450 Morningstar subindustry codes

## Structure

```
llm_finetuning/
├── data/               # Labeled CSVs — NOT committed to git
├── notebooks/          # Colab-ready training notebooks
├── scripts/            # Standalone Python training scripts
├── models/             # Saved checkpoints — NOT committed to git
├── results/            # Evaluation metrics, confusion matrices
└── requirements.txt    # Self-contained dependencies
```

## Baseline to Beat

| Metric        | TF-IDF + LinearSVM |
|---------------|--------------------|
| Macro F1 (T1) | 86.82%             |
| Macro F1 (T2) | TBD                |

## Data Format

Place your labeled CSV at `data/descriptions.csv` with columns:

```
description, mstar_code, mstar_label, sub_code, sub_label
```

## Quick Start (Colab)

Open `notebooks/01_finetune_deberta.ipynb` and run all cells.
The notebook is self-contained and handles installs, training, and evaluation.

---

*This project does not import from or depend on any other folder in this repository.*

---

## Recent Optimizations (Handling Extreme Class Imbalance)

Due to the extreme class imbalance in the 145/450 GECS taxonomy, the DeBERTa model initially struggled to outperform the TF-IDF + SVM baseline. To combat this and make the model "smarter", we introduced two major optimizations:

1. **Local LLM Data Augmentation:** 
   We created a standalone script (`data_augmentation/expand_descriptions.py`) that uses a local, 100% offline HuggingFace model (`google/flan-t5-base`). It iterates through the dataset and expands any description under 20 words into a rich 3-sentence profile, providing DeBERTa with more substantial text context for rare classes.

2. **PyTorch Inverse Class Weights:**
   We modified the raw training loop in `scripts/train_local.py`. It now automatically calculates the exact inverse frequency of every industry class in the dataset and passes a `class_weights` tensor directly into a custom `CrossEntropyLoss` function. This mathematically forces the model to heavily penalize errors made on rare minority classes, effectively neutralizing the class imbalance.
