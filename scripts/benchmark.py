"""
Benchmark: Cascade SVM vs Flat SVM vs DeBERTa baseline
Runs on the same holdout test set used for the DeBERTa 64% evaluation.
"""
from __future__ import annotations

import sys
import time
from collections import Counter
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.cascade_common import normalize_code
from scripts.cascade_predict import cascade_predict_sparse, load_cascade_assets

TEST_CSV   = ROOT / "llm_finetuning/data/task1_test.csv"
FLAT_MODEL = ROOT / "models/task1_svm_model.joblib"
FLAT_VEC   = ROOT / "models/task1_tfidf_vectorizer.pkl"
SEP        = "=" * 62


def load_test(path: Path) -> tuple[list[str], list[str]]:
    df     = pd.read_csv(path, dtype=str)
    texts  = df["text"].fillna("").tolist()
    labels = df["mstar_code"].map(normalize_code).tolist()
    return texts, labels


def print_metrics(y_true, y_pred, name: str) -> float:
    macro    = f1_score(y_true, y_pred, average="macro",    zero_division=0)
    weighted = f1_score(y_true, y_pred, average="weighted", zero_division=0)
    acc      = accuracy_score(y_true, y_pred)
    print(f"\n{SEP}")
    print(f"  {name}")
    print(SEP)
    print(f"  Macro F1    : {macro*100:6.2f}%")
    print(f"  Weighted F1 : {weighted*100:6.2f}%")
    print(f"  Accuracy    : {acc*100:6.2f}%")
    return macro


def long_tail_report(y_true, y_flat, y_cascade, min_support: int = 10):
    counts = Counter(y_true)
    rare   = {cls for cls, n in counts.items() if n <= min_support}
    if not rare:
        return
    idx    = [i for i, y in enumerate(y_true) if y in rare]
    yt     = [y_true[i]   for i in idx]
    yf     = [y_flat[i]   for i in idx]
    yc     = [y_cascade[i] for i in idx]
    f1_f   = f1_score(yt, yf, average="macro", zero_division=0)
    f1_c   = f1_score(yt, yc, average="macro", zero_division=0)
    print(f"\n{SEP}")
    print(f"  Long-Tail  (classes with <= {min_support} test examples)")
    print(SEP)
    print(f"  Rare classes  : {len(rare)}")
    print(f"  Rare samples  : {len(idx)}")
    print(f"  Flat SVM F1   on rare : {f1_f*100:6.2f}%")
    print(f"  Cascade  F1   on rare : {f1_c*100:6.2f}%")
    print(f"  Delta                 : {(f1_c - f1_f)*100:+.2f}%")


def main():
    print(SEP)
    print("  MGT 599 Capstone  —  Model Benchmark")
    print(SEP)

    print("\nLoading test set...")
    texts, y_true = load_test(TEST_CSV)
    n_classes = len(set(y_true))
    print(f"  {len(texts):,} samples  |  {n_classes} unique classes")

    # ── load assets ────────────────────────────────────────────
    print("\nLoading cascade assets...")
    assets  = load_cascade_assets()
    cascade_vec = assets["vectorizer"]

    print("Loading flat SVM...")
    flat_vec   = joblib.load(str(FLAT_VEC))
    flat_model = joblib.load(str(FLAT_MODEL))

    # unwrap breezeml wrapper if needed
    raw_clf = flat_model
    for attr in ["model", "_clf", "_estimator", "estimator"]:
        candidate = getattr(flat_model, attr, None)
        if candidate is not None and hasattr(candidate, "predict"):
            raw_clf = candidate
            break

    # ── vectorize once ─────────────────────────────────────────
    print("\nVectorizing all texts (cascade vectorizer)...")
    t0 = time.time()
    X_cascade = cascade_vec.transform(texts)
    print(f"  Done in {time.time()-t0:.1f}s  shape={X_cascade.shape}")

    print("Vectorizing all texts (flat SVM vectorizer)...")
    t0 = time.time()
    X_flat = flat_vec.transform(texts)
    print(f"  Done in {time.time()-t0:.1f}s  shape={X_flat.shape}")

    # ── cascade predictions ────────────────────────────────────
    print(f"\nRunning Cascade on {len(texts):,} samples...")
    t0, y_cascade = time.time(), []
    for i in range(X_cascade.shape[0]):
        result = cascade_predict_sparse(X_cascade[i], assets, top_n=1)
        y_cascade.append(normalize_code(result["mstar_code"]))
        if (i + 1) % 1000 == 0:
            pct = (i + 1) / len(texts) * 100
            print(f"  {i+1:>6}/{len(texts)}  ({pct:.0f}%)  {time.time()-t0:.0f}s elapsed")
    t_cascade = time.time() - t0
    cascade_f1 = print_metrics(y_true, y_cascade, "Cascade SVM  (Phase 1 — Legendary)")
    print(f"  Time : {t_cascade:.1f}s  |  {len(texts)/t_cascade:.0f} samples/sec")

    # ── flat SVM predictions ───────────────────────────────────
    print(f"\nRunning Flat SVM on {len(texts):,} samples...")
    t0 = time.time()
    y_flat_raw = raw_clf.predict(X_flat)
    y_flat     = [normalize_code(str(p)) for p in y_flat_raw]
    t_flat     = time.time() - t0
    flat_f1    = print_metrics(y_true, y_flat, "Flat SVM  (original baseline)")
    print(f"  Time : {t_flat:.1f}s  |  {len(texts)/t_flat:.0f} samples/sec")

    # ── summary ────────────────────────────────────────────────
    deberta_f1 = 0.6400
    delta_base = cascade_f1 - flat_f1
    delta_bert = cascade_f1 - deberta_f1

    print(f"\n{SEP}")
    print("  FINAL SUMMARY")
    print(SEP)
    print(f"  DeBERTa fine-tuned  (reported)  :  {deberta_f1*100:6.2f}%")
    print(f"  Flat SVM            (measured)  :  {flat_f1*100:6.2f}%")
    print(f"  Cascade SVM         (measured)  :  {cascade_f1*100:6.2f}%")
    print(f"  ---")
    print(f"  Cascade vs Flat SVM             :  {delta_base*100:+.2f}%")
    print(f"  Cascade vs DeBERTa              :  {delta_bert*100:+.2f}%")
    print(SEP)

    # ── long-tail ──────────────────────────────────────────────
    long_tail_report(y_true, y_flat, y_cascade, min_support=10)

    print(f"\n{SEP}")
    print("  Benchmark complete.")
    print(SEP)


if __name__ == "__main__":
    main()
