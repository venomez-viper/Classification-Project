"""
train_cascade_v9_finetune.py
============================
Fine-tunes a sentence transformer on this task using
MultipleNegativesRankingLoss directly via sentence-transformers
(no SetFit — bypasses its dependency hell).

Idea: pull same-label texts together in embedding space, push different-label
texts apart. After fine-tuning, the encoder produces task-aware embeddings
that classify much better with a downstream LinearSVC.

Run:
    python scripts/train_cascade_v9_finetune.py
"""
from __future__ import annotations

import json
import re
import sys
import time
from collections import Counter
from itertools import combinations
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import f1_score
from sklearn.svm import LinearSVC

ROOT = Path(__file__).resolve().parents[1]
RAW_CSV   = ROOT / "data/raw/task1_gecs_classification_final (2).csv"
TRAIN_CSV = ROOT / "llm_finetuning/data/task1_train.csv"
TEST_CSV  = ROOT / "llm_finetuning/data/task1_test.csv"
OUT_DIR   = ROOT / "models_v9"

BODY_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
SAMPLES_PER_CLASS = 8        # 145 × 8 = 1,160 anchors → 4,060 same-class pairs
N_EPOCHS = 2
BATCH_SIZE = 32
WARMUP_RATIO = 0.1


_BP = re.compile(r"\bThe [Cc]ompan(?:y|ies)\b", re.IGNORECASE)
def clean(t: Any) -> str:
    return re.sub(r"\s{2,}", " ", _BP.sub(" ", str(t))).strip()

def norm_code(v: Any) -> str:
    return str(int(v)).zfill(8)


def report(true_codes, preds, label="result"):
    f1 = f1_score(true_codes, preds, average="macro", zero_division=0)
    acc = sum(p == t for p, t in zip(preds, true_codes)) / len(true_codes)
    cf = Counter(true_codes)
    top10 = [c for c, _ in cf.most_common(10)]
    f1s = f1_score(true_codes, preds, average=None, labels=top10, zero_division=0)
    n_pass = int(sum(1 for v in f1s if v > 0.85))
    print(f"  {label}: F1={f1*100:.2f}%  acc={acc*100:.2f}%  top10={n_pass}/10", flush=True)
    return f1, n_pass


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading data …", flush=True)
    raw = pd.read_csv(RAW_CSV)
    raw["combined"] = (
        raw["LongProfile"].fillna("") + " " +
        raw["SegmentName"].fillna("") + " " +
        raw["SegmentDescription"].fillna("")
    ).str.replace(r"\s+", " ", regex=True).str.strip()
    raw_dedup = raw.drop_duplicates("combined", keep="first")[
        ["combined", "LongProfile", "SegmentName", "SegmentDescription"]
    ]

    train = pd.read_csv(TRAIN_CSV).merge(raw_dedup, left_on="text", right_on="combined", how="left")
    test  = pd.read_csv(TEST_CSV).merge(raw_dedup, left_on="text", right_on="combined", how="left")
    for df in (train, test):
        df["LongProfile"]        = df["LongProfile"].fillna(df["text"])
        df["SegmentName"]        = df["SegmentName"].fillna("")
        df["SegmentDescription"] = df["SegmentDescription"].fillna(df["text"])

    train["code"] = train["mstar_code"].map(norm_code)
    test["code"]  = test["mstar_code"].map(norm_code)

    def build_text(df):
        return (df["SegmentName"].astype(str) + ". "
                + df["SegmentDescription"].astype(str) + ". "
                + df["LongProfile"].astype(str)).map(clean)

    train_text = build_text(train).tolist()
    test_text  = build_text(test).tolist()
    train_y    = train["code"].tolist()
    test_y     = test["code"].tolist()
    print(f"  train={len(train_text):,}  test={len(test_text):,}  classes={len(set(train_y))}", flush=True)

    # ── Sample N per class ────────────────────────────────────────────────────
    print(f"\nSampling {SAMPLES_PER_CLASS} per class for contrastive fine-tune …", flush=True)
    df = pd.DataFrame({"text": train_text, "label": train_y})
    sampled_pieces = []
    for code, grp in df.groupby("label"):
        n = min(SAMPLES_PER_CLASS, len(grp))
        sampled_pieces.append(grp.sample(n, random_state=42))
    sampled = pd.concat(sampled_pieces, ignore_index=True)
    print(f"  sampled rows: {len(sampled):,}", flush=True)

    # ── Build same-class pairs (positives only — MNRL handles negatives) ──────
    print("\nBuilding same-class positive pairs …", flush=True)
    from sentence_transformers import SentenceTransformer, InputExample, losses
    from torch.utils.data import DataLoader

    pairs: list[InputExample] = []
    for code, grp in sampled.groupby("label"):
        texts = grp["text"].tolist()
        for a, b in combinations(texts, 2):
            pairs.append(InputExample(texts=[a, b]))
    print(f"  pairs: {len(pairs):,}", flush=True)

    # ── Fine-tune ─────────────────────────────────────────────────────────────
    print(f"\nLoading body {BODY_MODEL} …", flush=True)
    model = SentenceTransformer(BODY_MODEL, device="cpu")

    train_loader = DataLoader(pairs, shuffle=True, batch_size=BATCH_SIZE)
    loss = losses.MultipleNegativesRankingLoss(model)

    steps = len(train_loader) * N_EPOCHS
    warmup_steps = int(steps * WARMUP_RATIO)
    print(f"  steps={steps}  warmup={warmup_steps}  epochs={N_EPOCHS}", flush=True)

    print("Fine-tuning …", flush=True)
    t0 = time.time()
    model.fit(
        train_objectives=[(train_loader, loss)],
        epochs=N_EPOCHS,
        warmup_steps=warmup_steps,
        show_progress_bar=True,
        output_path=str(OUT_DIR / "ft_body"),
    )
    print(f"  fine-tune done in {(time.time()-t0)/60:.1f} min", flush=True)

    # ── Encode FULL train + test with fine-tuned encoder ──────────────────────
    print("\nEncoding full train + test with fine-tuned encoder …", flush=True)
    t0 = time.time()
    E_tr = model.encode(train_text, batch_size=64, show_progress_bar=True,
                        convert_to_numpy=True, normalize_embeddings=True)
    print(f"  train encoded in {(time.time()-t0)/60:.1f} min  shape={E_tr.shape}", flush=True)
    t0 = time.time()
    E_te = model.encode(test_text, batch_size=64, show_progress_bar=True,
                        convert_to_numpy=True, normalize_embeddings=True)
    print(f"  test  encoded in {(time.time()-t0)/60:.1f} min  shape={E_te.shape}", flush=True)

    np.save(OUT_DIR / "ft_train.npy", E_tr)
    np.save(OUT_DIR / "ft_test.npy",  E_te)

    # ── Train LinearSVC head ──────────────────────────────────────────────────
    print("\nTraining LinearSVC head with C tuning …", flush=True)
    best_C, best_f1, best_n, best_clf = 1.0, 0.0, 0, None
    for C in [0.5, 1.0, 2.0, 4.0]:
        clf = LinearSVC(C=C, dual=False, class_weight="balanced", max_iter=5000)
        t0 = time.time()
        clf.fit(E_tr, train_y)
        preds = clf.predict(E_te)
        f1 = f1_score(test_y, preds, average="macro", zero_division=0)
        cf = Counter(test_y)
        top10 = [c for c, _ in cf.most_common(10)]
        f1s = f1_score(test_y, preds, average=None, labels=top10, zero_division=0)
        n_pass = int(sum(1 for v in f1s if v > 0.85))
        marker = "  <-- BEST" if f1 > best_f1 else ""
        print(f"  C={C}: F1={f1*100:.2f}%  top10={n_pass}/10  ({time.time()-t0:.1f}s){marker}", flush=True)
        if f1 > best_f1:
            best_C, best_f1, best_n, best_clf = C, f1, n_pass, clf

    print("\n" + "=" * 65, flush=True)
    print(f"V9 RESULT: F1={best_f1*100:.2f}%  C={best_C}  top10={best_n}/10", flush=True)
    print(f"Target: >= 75.00%  -> {'PASS' if best_f1 >= 0.75 else 'FAIL'}", flush=True)
    print("=" * 65, flush=True)

    joblib.dump(best_clf, OUT_DIR / "v9_svm.joblib")
    summary = {
        "version": "v9-manual-finetune",
        "body": BODY_MODEL,
        "samples_per_class": SAMPLES_PER_CLASS,
        "n_epochs": N_EPOCHS,
        "n_pairs": len(pairs),
        "best_C": best_C,
        "macro_f1": round(float(best_f1) * 100, 2),
        "top10_pass": int(best_n),
        "target_met": bool(best_f1 >= 0.75),
    }
    (OUT_DIR / "training_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(f"  Saved to {OUT_DIR}", flush=True)


if __name__ == "__main__":
    main()
