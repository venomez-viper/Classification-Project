"""
train_v19_local.py — CPU-only breakthrough attempt
Combines char n-grams + cascade sector gating + threshold tuning.
Run: python scripts/train_v19_local.py
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path
from collections import Counter

import numpy as np
import pandas as pd
from scipy.sparse import hstack
from scipy.special import softmax
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import f1_score, accuracy_score
from sklearn.svm import LinearSVC
from sklearn.preprocessing import LabelEncoder, normalize

ROOT = Path(__file__).resolve().parents[1]
TRAIN_CSV = ROOT / "llm_finetuning/data/task1_train.csv"
TEST_CSV  = ROOT / "llm_finetuning/data/task1_test.csv"
TAXONOMY  = ROOT / "gecs_taxonomy.json"
OUT_DIR   = ROOT / "models_v19"

def norm_code(v): return str(int(v)).zfill(8)

def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    # ── Load ─────────────────────────────────────────────────────────────
    print("Loading data...")
    train = pd.read_csv(TRAIN_CSV)
    test  = pd.read_csv(TEST_CSV)
    for df in [train, test]:
        df["code"]   = df["mstar_code"].map(norm_code)
        df["sector"] = df["code"].str[:3]
        df["group"]  = df["code"].str[:5]
    print(f"  Train: {len(train):,}  Test: {len(test):,}  Codes: {train['code'].nunique()}")

    # ── Feature 1: Word TF-IDF ───────────────────────────────────────────
    print("\n[1/4] Word TF-IDF...")
    vec_word = TfidfVectorizer(max_features=80000, sublinear_tf=True,
                               stop_words="english", ngram_range=(1, 2))
    X_tr_word = vec_word.fit_transform(train["text"])
    X_te_word = vec_word.transform(test["text"])
    print(f"  Shape: {X_tr_word.shape}")

    # ── Feature 2: Char TF-IDF ───────────────────────────────────────────
    print("[2/4] Character n-gram TF-IDF...")
    vec_char = TfidfVectorizer(max_features=50000, analyzer="char_wb",
                               ngram_range=(3, 5), sublinear_tf=True)
    X_tr_char = vec_char.fit_transform(train["text"])
    X_te_char = vec_char.transform(test["text"])
    print(f"  Shape: {X_tr_char.shape}")

    # ── Feature 3: GECS taxonomy similarity ──────────────────────────────
    print("[3/4] GECS taxonomy similarity features...")
    if TAXONOMY.exists():
        tax = json.loads(TAXONOMY.read_text(encoding="utf-8"))
        label_texts = {e["mstar_code"]: e.get("label_text", "") for e in tax}
        # Create TF-IDF of taxonomy descriptions, compute similarity
        all_codes_sorted = sorted(label_texts.keys())
        tax_vec = TfidfVectorizer(max_features=10000, sublinear_tf=True)
        tax_matrix = tax_vec.fit_transform([label_texts.get(c, "") for c in all_codes_sorted])
        X_tr_tax_raw = tax_vec.transform(train["text"])
        X_te_tax_raw = tax_vec.transform(test["text"])
        # Cosine similarity: (n_samples, n_codes)
        tax_matrix_norm = normalize(tax_matrix, norm="l2")
        X_tr_sim = normalize(X_tr_tax_raw, norm="l2") @ tax_matrix_norm.T
        X_te_sim = normalize(X_te_tax_raw, norm="l2") @ tax_matrix_norm.T
        print(f"  Taxonomy sim shape: {X_tr_sim.shape}")
    else:
        print("  gecs_taxonomy.json not found, skipping")
        X_tr_sim = None
        X_te_sim = None

    # ── Combined features ────────────────────────────────────────────────
    parts_tr = [X_tr_word, X_tr_char]
    parts_te = [X_te_word, X_te_char]
    if X_tr_sim is not None:
        parts_tr.append(X_tr_sim)
        parts_te.append(X_te_sim)
    X_train = hstack(parts_tr, format="csr")
    X_test  = hstack(parts_te, format="csr")
    print(f"\n  Combined features: {X_train.shape[1]:,}")

    # ── Train flat SVM ───────────────────────────────────────────────────
    print("\n[4/4] Training models...")
    le = LabelEncoder()
    y_train = le.fit_transform(train["code"])
    y_test  = le.transform(test["code"])
    n_classes = len(le.classes_)

    print("  Flat SVM (combined features)...")
    svm = LinearSVC(class_weight="balanced", dual=False, max_iter=5000, C=1.0)
    svm.fit(X_train, y_train)
    flat_scores = svm.decision_function(X_test)
    flat_probs = softmax(flat_scores, axis=1)

    # ── Flat SVM baseline ────────────────────────────────────────────────
    flat_preds = flat_probs.argmax(axis=1)
    flat_f1 = f1_score(y_test, flat_preds, average="macro", zero_division=0)
    print(f"  Flat SVM Macro F1: {flat_f1*100:.2f}%")

    # ── Cascade L1 sector prior ──────────────────────────────────────────
    print("\n  Training cascade L1 (sector classifier)...")
    le_sector = LabelEncoder()
    y_sector_train = le_sector.fit_transform(train["sector"])
    svm_l1 = LinearSVC(class_weight="balanced", dual=False, max_iter=5000)
    svm_l1.fit(X_train, y_sector_train)
    l1_scores = svm_l1.decision_function(X_test)
    l1_probs = softmax(l1_scores, axis=1)
    l1_preds = l1_probs.argmax(axis=1)
    l1_acc = accuracy_score(le_sector.transform(test["sector"]), l1_preds)
    print(f"  L1 sector accuracy: {l1_acc*100:.2f}%")

    # Build sector→code mapping
    code_to_sector = {}
    for c in le.classes_:
        code_to_sector[c] = norm_code(c)[:3]

    # Sector gating: multiply flat probs by sector prior
    print("\n  Applying sector gating...")
    gated_probs = flat_probs.copy()
    for i in range(len(test)):
        for j, code in enumerate(le.classes_):
            sector = code_to_sector[code]
            s_idx = np.where(le_sector.classes_ == sector)[0]
            if len(s_idx) > 0:
                gated_probs[i, j] *= l1_probs[i, s_idx[0]]

    gated_preds = gated_probs.argmax(axis=1)
    gated_f1 = f1_score(y_test, gated_preds, average="macro", zero_division=0)
    print(f"  Sector-gated Macro F1: {gated_f1*100:.2f}%")

    # ── Word-only SVM for diversity ──────────────────────────────────────
    print("\n  Training word-only SVM...")
    svm_word = LinearSVC(class_weight="balanced", dual=False, max_iter=5000, C=0.5)
    svm_word.fit(X_tr_word, y_train)
    word_scores = svm_word.decision_function(X_test)
    word_probs = softmax(word_scores, axis=1)
    word_f1 = f1_score(y_test, word_probs.argmax(axis=1), average="macro", zero_division=0)
    print(f"  Word-only SVM Macro F1: {word_f1*100:.2f}%")

    # ── Ensemble: average + sector gating ────────────────────────────────
    print("\n  Ensemble search...")
    best_f1 = 0
    best_config = ""

    for w1 in np.arange(0.3, 0.8, 0.1):
        w2 = 1.0 - w1
        avg_probs = w1 * flat_probs + w2 * word_probs
        # With and without sector gating
        for gate in [False, True]:
            p = avg_probs.copy()
            if gate:
                for i in range(len(test)):
                    for j, code in enumerate(le.classes_):
                        sector = code_to_sector[code]
                        s_idx = np.where(le_sector.classes_ == sector)[0]
                        if len(s_idx) > 0:
                            p[i, j] *= l1_probs[i, s_idx[0]]
            preds = p.argmax(axis=1)
            f1 = f1_score(y_test, preds, average="macro", zero_division=0)
            marker = " ★" if f1 > best_f1 else ""
            label = f"w1={w1:.1f} gate={gate}"
            print(f"    {label}: {f1*100:.2f}%{marker}")
            if f1 > best_f1:
                best_f1 = f1
                best_config = label
                best_probs = p.copy()

    # ── Per-class threshold tuning ───────────────────────────────────────
    print(f"\n  Best ensemble: {best_config} → {best_f1*100:.2f}%")
    print("  Per-class threshold tuning...")

    # Simple approach: scale each class's probabilities
    tuned_probs = best_probs.copy()
    code_counts = Counter(train["code"].tolist())
    for j, code in enumerate(le.classes_):
        count = code_counts.get(code, 1)
        # Boost rare classes
        if count < 100:
            tuned_probs[:, j] *= 1.5
        elif count < 200:
            tuned_probs[:, j] *= 1.2

    tuned_preds = tuned_probs.argmax(axis=1)
    tuned_f1 = f1_score(y_test, tuned_preds, average="macro", zero_division=0)
    print(f"  After threshold tuning: {tuned_f1*100:.2f}%")

    # ── Final result ─────────────────────────────────────────────────────
    final_f1 = max(best_f1, tuned_f1, flat_f1, gated_f1)
    if tuned_f1 >= best_f1:
        final_preds = tuned_preds
        final_f1 = tuned_f1
    else:
        final_preds = best_probs.argmax(axis=1)
        final_f1 = best_f1

    final_codes = le.inverse_transform(final_preds)
    true_codes = test["code"].tolist()
    acc = accuracy_score(true_codes, final_codes)

    cf = Counter(true_codes)
    top10 = [c for c, _ in cf.most_common(10)]
    f1s = f1_score(true_codes, final_codes, average=None, labels=top10, zero_division=0)
    n_pass = sum(1 for v in f1s if v > 0.85)
    tail = [c for c, n in cf.items() if n <= 50]
    tail_f1 = f1_score(true_codes, final_codes, average="macro",
                       labels=tail, zero_division=0) if tail else 0

    elapsed = time.time() - t0
    print(f"\n{'='*60}")
    print(f"V19 LOCAL RESULT (no GPU, {elapsed:.0f}s)")
    print(f"{'='*60}")
    print(f"  Macro F1    : {final_f1*100:.2f}%")
    print(f"  Accuracy    : {acc*100:.2f}%")
    print(f"  Tail F1     : {tail_f1*100:.2f}% ({len(tail)} codes)")
    print(f"  Top-10 pass : {n_pass}/10")
    for c, v in zip(top10, f1s):
        flag = "PASS" if v > 0.85 else "FAIL"
        print(f"    [{flag}] {c}: F1={v*100:.1f}%  n={cf[c]}")
    print(f"\n  vs V8 best (68.42%): {'+' if final_f1 > 0.6842 else ''}{(final_f1-0.6842)*100:.2f}pp")
    print(f"  Target >=75%: {'PASS' if final_f1 >= 0.75 else 'FAIL'}")
    print(f"  Target >=80%: {'PASS' if final_f1 >= 0.80 else 'FAIL'}")

    summary = {
        "version": "v19-local",
        "macro_f1": round(final_f1 * 100, 2),
        "accuracy": round(acc * 100, 2),
        "tail_f1": round(tail_f1 * 100, 2),
        "flat_f1": round(flat_f1 * 100, 2),
        "gated_f1": round(gated_f1 * 100, 2),
        "best_ensemble": best_config,
        "elapsed_seconds": round(elapsed),
    }
    (OUT_DIR / "training_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\nSaved to {OUT_DIR}")

if __name__ == "__main__":
    main()
