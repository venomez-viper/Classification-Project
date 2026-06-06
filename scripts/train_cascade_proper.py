"""
train_cascade_proper.py
-----------------------
Trains the Task 1 cascade on the proper 80/20 train split
(llm_finetuning/data/task1_train.csv — 42,868 rows) rather than
the full 53,585-row dataset that caused the evaluation data leak.

Saves artifacts to models_v2/ so the old models stay intact for comparison.
Run:
    python scripts/train_cascade_proper.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import f1_score
from sklearn.svm import LinearSVC

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TRAIN_CSV = ROOT / "llm_finetuning/data/task1_train.csv"
TEST_CSV  = ROOT / "llm_finetuning/data/task1_test.csv"
OUT_DIR   = ROOT / "models_v2"

# Identical hyperparameters to the original — Stage 1 is about honest evaluation only
MAX_FEATURES = 50000
NGRAM_RANGE  = (1, 2)
MAX_ITER     = 5000


def normalize_code(value: Any) -> str:
    s = str(int(value))
    return s.zfill(8)


def softmax(scores: np.ndarray) -> np.ndarray:
    scores = np.asarray(scores, dtype=np.float64)
    scores -= scores.max()
    e = np.exp(scores)
    return e / e.sum()


def fit_artifact(X_sparse, labels, max_iter: int) -> dict[str, Any]:
    unique = sorted(set(str(l) for l in labels))
    if len(unique) == 1:
        return {"type": "constant", "value": unique[0]}
    model = LinearSVC(class_weight="balanced", dual=False, max_iter=max_iter)
    model.fit(X_sparse, labels)
    return {"type": "svm", "model": model}


def predict_artifact(artifact: dict, X_sparse) -> tuple[str, float]:
    if artifact["type"] == "constant":
        return str(artifact["value"]), 100.0
    model = artifact["model"]
    scores = model.decision_function(X_sparse)
    classes = np.asarray(model.classes_, dtype=str)
    if np.ndim(scores) == 1:
        margins = np.array([-scores[0], scores[0]], dtype=np.float64)
    else:
        margins = np.asarray(scores[0], dtype=np.float64)
    probs = softmax(margins)
    best = int(np.argmax(probs))
    return str(classes[best]), round(float(probs[best]) * 100, 1)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # ── Load splits ──────────────────────────────────────────────────────────
    print("Loading train split …")
    train = pd.read_csv(TRAIN_CSV)
    test  = pd.read_csv(TEST_CSV)

    train["code"]        = train["mstar_code"].map(normalize_code)
    train["sector_code"] = train["code"].str[:3]
    train["group_code"]  = train["code"].str[:5]

    test["code"]         = test["mstar_code"].map(normalize_code)
    test["sector_code"]  = test["code"].str[:3]
    test["group_code"]   = test["code"].str[:5]

    print(f"  Train: {len(train):,} rows | {train['code'].nunique()} classes")
    print(f"  Test:  {len(test):,} rows  | {test['code'].nunique()} classes")

    # ── Vectorize ─────────────────────────────────────────────────────────────
    print("\nFitting TF-IDF vectorizer …")
    vec = TfidfVectorizer(
        max_features=MAX_FEATURES,
        sublinear_tf=True,
        stop_words="english",
        ngram_range=NGRAM_RANGE,
    )
    X_train = vec.fit_transform(train["text"])
    X_test  = vec.transform(test["text"])
    print(f"  Vocabulary size: {len(vec.vocabulary_):,}")

    # ── L1: sector ────────────────────────────────────────────────────────────
    print("\nTraining L1 (sector, 11 classes) …")
    l1_artifact = fit_artifact(X_train, train["sector_code"], MAX_ITER)

    # ── L2: group per sector ──────────────────────────────────────────────────
    print("Training L2 (group, one model per sector) …")
    l2_artifacts: dict[str, Any] = {}
    for sector, grp in train.groupby("sector_code", sort=True):
        idx = grp.index
        l2_artifacts[str(sector)] = fit_artifact(
            X_train[idx], grp["group_code"], MAX_ITER
        )
    n_const_l2 = sum(1 for a in l2_artifacts.values() if a["type"] == "constant")
    print(f"  L2 artifacts: {len(l2_artifacts)} total, {n_const_l2} constants")

    # ── L3: code per group ────────────────────────────────────────────────────
    print("Training L3 (code, one model per group) …")
    l3_artifacts: dict[str, Any] = {}
    for group, grp in train.groupby("group_code", sort=True):
        idx = grp.index
        l3_artifacts[str(group)] = fit_artifact(
            X_train[idx], grp["code"], MAX_ITER
        )
    n_const_l3 = sum(1 for a in l3_artifacts.values() if a["type"] == "constant")
    print(f"  L3 artifacts: {len(l3_artifacts)} total, {n_const_l3} constants")

    # ── Evaluate on test set ──────────────────────────────────────────────────
    print("\nEvaluating on test set …")

    preds, sector_preds, group_preds = [], [], []
    for i in range(X_test.shape[0]):
        Xi = X_test[i]

        sector, _ = predict_artifact(l1_artifact, Xi)
        l2 = l2_artifacts.get(sector)
        if l2 is None:
            # Fallback: pick sector with most training samples
            sector = train["sector_code"].value_counts().idxmax()
            l2 = l2_artifacts[sector]
        group, _ = predict_artifact(l2, Xi)

        l3 = l3_artifacts.get(group)
        if l3 is None:
            group = (train[train["sector_code"] == sector]["group_code"]
                     .value_counts().idxmax())
            l3 = l3_artifacts[group]
        code, _ = predict_artifact(l3, Xi)

        sector_preds.append(sector)
        group_preds.append(group)
        preds.append(code)

        if (i + 1) % 1000 == 0:
            print(f"  {i+1:,}/{len(test):,} …")

    true_codes   = test["code"].tolist()
    true_sectors = test["sector_code"].tolist()
    true_groups  = test["group_code"].tolist()

    l1_acc  = sum(sp == st for sp, st in zip(sector_preds, true_sectors)) / len(true_sectors)
    l2_acc  = sum(gp == gt for gp, gt in zip(group_preds, true_groups))   / len(true_groups)
    macro_f1 = f1_score(true_codes, preds, average="macro", zero_division=0)

    # Top-10 class F1
    from collections import Counter
    code_freq   = Counter(true_codes)
    top10_codes = [c for c, _ in code_freq.most_common(10)]
    f1_top10    = f1_score(true_codes, preds, average=None, labels=top10_codes, zero_division=0)

    # Error propagation
    l1_errors = sum(sp != st for sp, st in zip(sector_preds, true_sectors))
    l2_errors = sum(
        gp != gt
        for sp, st, gp, gt in zip(sector_preds, true_sectors, group_preds, true_groups)
        if sp == st
    )
    l3_errors = sum(
        p != t
        for sp, st, gp, gt, p, t in zip(
            sector_preds, true_sectors, group_preds, true_groups, preds, true_codes
        )
        if sp == st and gp == gt
    )

    print()
    print("=" * 55)
    print("HONEST EVALUATION — trained on train split only")
    print("=" * 55)
    print(f"  L1 Sector accuracy : {l1_acc * 100:.2f}%")
    print(f"  L2 Group  accuracy : {l2_acc * 100:.2f}%")
    print(f"  L3 Macro F1        : {macro_f1 * 100:.2f}%")
    print()
    print("  Error propagation:")
    total = len(true_codes)
    print(f"    L1 wrong         : {l1_errors:,} ({l1_errors/total*100:.1f}%)")
    print(f"    L2 wrong|L1 ok   : {l2_errors:,} ({l2_errors/total*100:.1f}%)")
    print(f"    L3 wrong|L2 ok   : {l3_errors:,} ({l3_errors/total*100:.1f}%)")
    print()
    print("  Top-10 class F1 (case criterion: > 85%):")
    for code, f1_val in zip(top10_codes, f1_top10):
        status = "PASS" if f1_val > 0.85 else "FAIL"
        print(f"    [{status}] {code}: {f1_val*100:.1f}%  n={code_freq[code]}")

    # ── Save artifacts ────────────────────────────────────────────────────────
    print(f"\nSaving artifacts to {OUT_DIR} …")
    joblib.dump(vec,          OUT_DIR / "cascade_vectorizer.pkl")
    joblib.dump(l1_artifact,  OUT_DIR / "cascade_L1_svm.joblib")
    joblib.dump(l2_artifacts, OUT_DIR / "cascade_L2_models.joblib")
    joblib.dump(l3_artifacts, OUT_DIR / "cascade_L3_models.joblib")

    summary = {
        "trained_on":    "task1_train.csv (80% split, no leakage)",
        "train_rows":    int(len(train)),
        "test_rows":     int(len(test)),
        "sector_count":  int(train["sector_code"].nunique()),
        "group_count":   int(train["group_code"].nunique()),
        "code_count":    int(train["code"].nunique()),
        "macro_f1":      round(float(macro_f1) * 100, 2),
        "l1_accuracy":   round(float(l1_acc) * 100, 2),
        "l2_accuracy":   round(float(l2_acc) * 100, 2),
        "vectorizer":    {
            "max_features": MAX_FEATURES,
            "ngram_range":  list(NGRAM_RANGE),
            "sublinear_tf": True,
        },
    }
    (OUT_DIR / "cascade_training_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print("Done.")
    print(f"\nHonest Macro F1: {macro_f1 * 100:.2f}%")


if __name__ == "__main__":
    main()
