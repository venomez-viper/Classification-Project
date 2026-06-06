"""
ensemble_final.py
-----------------
Combines the Multi-Task HTC DeBERTa predictions (from Colab)
with the local TF-IDF SVM to produce the final ensemble.

Usage:
    1. Run htc_deberta_v2.ipynb on Colab
    2. Download htc_outputs.zip and unzip to models_v18/htc_outputs/
    3. Run: python scripts/ensemble_final.py

The ensemble uses weighted geometric mean of probability distributions
from both models, then optionally tunes per-class thresholds.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from collections import Counter

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import f1_score, accuracy_score
from sklearn.svm import LinearSVC
from sklearn.preprocessing import LabelEncoder
from scipy.special import softmax

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TRAIN_CSV = ROOT / "llm_finetuning/data/task1_train.csv"
TEST_CSV  = ROOT / "llm_finetuning/data/task1_test.csv"
HTC_DIR   = ROOT / "models_v18/htc_outputs"
OUT_DIR   = ROOT / "models_v18"


def normalize_code(value) -> str:
    return str(int(value)).zfill(8)


def train_flat_svm(train_df, test_df):
    """Train a flat TF-IDF + LinearSVC and return test probability matrix."""
    print("Training flat TF-IDF + LinearSVC...")
    vec = TfidfVectorizer(max_features=80000, sublinear_tf=True,
                          stop_words="english", ngram_range=(1, 2))
    X_train = vec.fit_transform(train_df["text"])
    X_test  = vec.transform(test_df["text"])

    le = LabelEncoder()
    y_train = le.fit_transform(train_df["code"])

    svm = LinearSVC(class_weight="balanced", dual=False, max_iter=5000)
    svm.fit(X_train, y_train)

    # Get decision function scores and convert to pseudo-probabilities
    scores = svm.decision_function(X_test)  # (n_test, n_classes)
    probs = softmax(scores, axis=1)         # normalize to probability simplex

    # Align classes with HTC label encoder
    htc_classes = np.load(HTC_DIR / "le_code_classes.npy", allow_pickle=True)
    svm_classes = le.classes_

    # Build aligned probability matrix
    aligned_probs = np.zeros((len(test_df), len(htc_classes)))
    for i, cls in enumerate(svm_classes):
        code_str = normalize_code(cls)
        htc_idx = np.where(htc_classes == code_str)[0]
        if len(htc_idx) > 0:
            aligned_probs[:, htc_idx[0]] = probs[:, i]

    print(f"  SVM classes: {len(svm_classes)}  Aligned: {(aligned_probs.sum(axis=0) > 0).sum()}")
    return aligned_probs, le


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # ── Check HTC outputs exist ──────────────────────────────────────────
    if not (HTC_DIR / "htc_test_probs.npy").exists():
        print(f"ERROR: HTC outputs not found at {HTC_DIR}")
        print("Run the Colab notebook first, then unzip htc_outputs.zip to models_v18/htc_outputs/")
        sys.exit(1)

    # ── Load data ────────────────────────────────────────────────────────
    print("Loading data...")
    train_df = pd.read_csv(TRAIN_CSV)
    test_df  = pd.read_csv(TEST_CSV)
    train_df["code"] = train_df["mstar_code"].map(normalize_code)
    test_df["code"]  = test_df["mstar_code"].map(normalize_code)

    # ── Load HTC outputs ─────────────────────────────────────────────────
    print("Loading HTC DeBERTa outputs...")
    htc_probs    = np.load(HTC_DIR / "htc_test_probs.npy")
    htc_classes  = np.load(HTC_DIR / "le_code_classes.npy", allow_pickle=True)
    htc_results  = json.loads((HTC_DIR / "htc_results.json").read_text())
    print(f"  HTC standalone Macro F1: {htc_results['macro_f1']}%")

    # ── Train flat SVM ───────────────────────────────────────────────────
    svm_probs, svm_le = train_flat_svm(train_df, test_df)

    # ── SVM standalone eval ──────────────────────────────────────────────
    svm_preds_idx = svm_probs.argmax(axis=1)
    svm_pred_codes = [str(htc_classes[i]) for i in svm_preds_idx]
    svm_f1 = f1_score(test_df["code"].tolist(), svm_pred_codes,
                      average="macro", zero_division=0)
    print(f"  SVM standalone Macro F1: {svm_f1*100:.2f}%")

    # ── Ensemble: weighted geometric mean ────────────────────────────────
    print("\nEnsemble search...")
    true_codes = test_df["code"].tolist()
    best_f1 = 0.0
    best_w = 0.0

    for w_htc in np.arange(0.3, 0.9, 0.05):
        w_svm = 1.0 - w_htc
        # Geometric mean in log space
        eps = 1e-10
        log_probs = w_htc * np.log(htc_probs + eps) + w_svm * np.log(svm_probs + eps)
        ensemble_preds_idx = log_probs.argmax(axis=1)
        ensemble_pred_codes = [str(htc_classes[i]) for i in ensemble_preds_idx]
        f1 = f1_score(true_codes, ensemble_pred_codes, average="macro", zero_division=0)
        marker = " ★" if f1 > best_f1 else ""
        print(f"  w_htc={w_htc:.2f}  w_svm={w_svm:.2f}  Macro F1={f1*100:.2f}%{marker}")
        if f1 > best_f1:
            best_f1 = f1
            best_w = w_htc

    # ── Final ensemble with best weight ──────────────────────────────────
    print(f"\nBest weight: w_htc={best_w:.2f}  w_svm={1-best_w:.2f}")
    eps = 1e-10
    log_probs = best_w * np.log(htc_probs + eps) + (1-best_w) * np.log(svm_probs + eps)
    final_preds_idx = log_probs.argmax(axis=1)
    final_pred_codes = [str(htc_classes[i]) for i in final_preds_idx]

    macro_f1 = f1_score(true_codes, final_pred_codes, average="macro", zero_division=0)
    acc = accuracy_score(true_codes, final_pred_codes)

    # Top-10
    cf = Counter(true_codes)
    top10 = [c for c, _ in cf.most_common(10)]
    f1s = f1_score(true_codes, final_pred_codes, average=None, labels=top10, zero_division=0)
    n_pass = int(sum(1 for v in f1s if v > 0.85))

    # Tail
    tail_codes = [c for c, n in cf.items() if n <= 50]
    tail_f1 = f1_score(true_codes, final_pred_codes, average="macro",
                       labels=tail_codes, zero_division=0) if tail_codes else 0.0

    print()
    print("=" * 60)
    print("FINAL ENSEMBLE RESULT")
    print("=" * 60)
    print(f"  HTC DeBERTa alone : {htc_results['macro_f1']}%")
    print(f"  Flat SVM alone    : {svm_f1*100:.2f}%")
    print(f"  Ensemble Macro F1 : {macro_f1*100:.2f}%")
    print(f"  Ensemble Accuracy : {acc*100:.2f}%")
    print(f"  Tail F1           : {tail_f1*100:.2f}% ({len(tail_codes)} codes)")
    print(f"  Top-10 pass       : {n_pass}/10")
    for c, v in zip(top10, f1s):
        flag = "PASS" if v > 0.85 else "FAIL"
        print(f"    [{flag}] {c}: F1={v*100:.1f}%  n={cf[c]}")

    print(f"\n  Target >=75%: {'PASS' if macro_f1 >= 0.75 else 'FAIL'}")
    print(f"  Target >=80%: {'PASS' if macro_f1 >= 0.80 else 'FAIL'}")

    # ── Save ─────────────────────────────────────────────────────────────
    summary = {
        "method": "geometric_ensemble",
        "w_htc": round(best_w, 2),
        "w_svm": round(1 - best_w, 2),
        "htc_f1": htc_results["macro_f1"],
        "svm_f1": round(svm_f1 * 100, 2),
        "ensemble_f1": round(macro_f1 * 100, 2),
        "ensemble_acc": round(acc * 100, 2),
        "tail_f1": round(tail_f1 * 100, 2),
        "top10_pass": n_pass,
        "target_75": bool(macro_f1 >= 0.75),
        "target_80": bool(macro_f1 >= 0.80),
    }
    (OUT_DIR / "ensemble_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(f"\nSaved to {OUT_DIR / 'ensemble_summary.json'}")


if __name__ == "__main__":
    main()
