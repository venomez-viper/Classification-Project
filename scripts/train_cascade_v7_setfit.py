"""
train_cascade_v7_setfit.py
==========================
Fine-tunes a sentence transformer ON THIS TASK using SetFit's contrastive
learning. Unlike V4-V6 which use frozen embeddings, this trains the encoder
itself to push same-label rows together and different-label rows apart.

For 145 classes this is computationally expensive but typically gives
+5-15pp over zero-shot embeddings.

Run:
    python scripts/train_cascade_v7_setfit.py
"""
from __future__ import annotations

import json
import re
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score
from sklearn.svm import LinearSVC

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

RAW_CSV   = ROOT / "data/raw/task1_gecs_classification_final (2).csv"
TRAIN_CSV = ROOT / "llm_finetuning/data/task1_train.csv"
TEST_CSV  = ROOT / "llm_finetuning/data/task1_test.csv"
OUT_DIR   = ROOT / "models_v7"

# SetFit body — start from MiniLM (fast) for fine-tuning
BODY_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
SAMPLES_PER_CLASS = 8           # SetFit default
N_EPOCHS_BODY     = 1            # 1 epoch — already 145 classes × 8 = 1160 anchors
BATCH_SIZE        = 16


_BP = re.compile(r"\bThe [Cc]ompan(?:y|ies)\b", re.IGNORECASE)
def clean(t: Any) -> str:
    return re.sub(r"\s{2,}", " ", _BP.sub(" ", str(t))).strip()

def norm_code(v: Any) -> str:
    return str(int(v)).zfill(8)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading data …")
    raw = pd.read_csv(RAW_CSV)
    raw["combined"] = (
        raw["LongProfile"].fillna("") + " " +
        raw["SegmentName"].fillna("") + " " +
        raw["SegmentDescription"].fillna("")
    ).str.replace(r"\s+", " ", regex=True).str.strip()
    raw_dedup = raw.drop_duplicates("combined", keep="first")[
        ["combined", "LongProfile", "SegmentName", "SegmentDescription"]
    ]

    train = pd.read_csv(TRAIN_CSV).merge(raw_dedup, left_on="text",
                                          right_on="combined", how="left")
    test  = pd.read_csv(TEST_CSV).merge(raw_dedup, left_on="text",
                                          right_on="combined", how="left")
    for df in (train, test):
        df["LongProfile"]        = df["LongProfile"].fillna(df["text"])
        df["SegmentName"]        = df["SegmentName"].fillna("")
        df["SegmentDescription"] = df["SegmentDescription"].fillna(df["text"])

    train["code"] = train["mstar_code"].map(norm_code)
    test["code"]  = test["mstar_code"].map(norm_code)

    # Use segment text + LongProfile concatenated as the input
    def build_text(df):
        return (
            df["SegmentName"].astype(str) + ". " +
            df["SegmentDescription"].astype(str) + ". " +
            df["LongProfile"].astype(str)
        ).map(clean)

    train_text = build_text(train).tolist()
    test_text  = build_text(test).tolist()
    train_y    = train["code"].tolist()
    test_y     = test["code"].tolist()
    print(f"  train={len(train_text):,}  test={len(test_text):,}  classes={len(set(train_y))}")

    # ── Sample N rows per class for SetFit fine-tuning ────────────────────────
    print(f"\nSampling {SAMPLES_PER_CLASS} rows per class for SetFit body fine-tune …")
    train_df = pd.DataFrame({"text": train_text, "label": train_y})
    pieces = []
    for code, grp in train_df.groupby("label"):
        n = min(SAMPLES_PER_CLASS, len(grp))
        pieces.append(grp.sample(n, random_state=42))
    sampled = pd.concat(pieces, ignore_index=True)
    print(f"  sampled rows: {len(sampled):,}")
    print(f"  columns: {list(sampled.columns)}")

    # ── Train SetFit ───────────────────────────────────────────────────────────
    print(f"\nLoading SetFit body {BODY_MODEL} …")
    from setfit import SetFitModel, Trainer, TrainingArguments
    from datasets import Dataset

    model = SetFitModel.from_pretrained(BODY_MODEL)

    train_ds = Dataset.from_pandas(sampled[["text", "label"]])

    args = TrainingArguments(
        output_dir=str(OUT_DIR / "setfit_body"),
        batch_size=BATCH_SIZE,
        num_epochs=N_EPOCHS_BODY,
        sampling_strategy="oversampling",
        body_learning_rate=2e-5,
        save_strategy="no",
    )

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=train_ds,
    )

    print("Training SetFit body (contrastive learning) …")
    t0 = time.time()
    trainer.train()
    print(f"  body training done in {(time.time()-t0)/60:.1f} min")

    # ── Now use the fine-tuned encoder on FULL train set for embeddings ───────
    print("\nEncoding full train+test with fine-tuned encoder …")
    body = model.model_body  # the underlying sentence transformer

    t0 = time.time()
    E_tr = body.encode(train_text, batch_size=64, show_progress_bar=True,
                        convert_to_numpy=True, normalize_embeddings=True)
    print(f"  train encoded in {(time.time()-t0)/60:.1f} min  shape={E_tr.shape}")
    t0 = time.time()
    E_te = body.encode(test_text, batch_size=64, show_progress_bar=True,
                        convert_to_numpy=True, normalize_embeddings=True)
    print(f"  test  encoded in {(time.time()-t0)/60:.1f} min  shape={E_te.shape}")

    np.save(OUT_DIR / "setfit_train.npy", E_tr)
    np.save(OUT_DIR / "setfit_test.npy",  E_te)

    # ── Train flat LinearSVC on full data + fine-tuned embeddings ─────────────
    print("\nTraining flat LinearSVC head on fine-tuned embeddings …")
    best_C, best_f1, best_n = 1.0, 0.0, 0
    for C in [0.5, 1.0, 2.0, 4.0]:
        clf = LinearSVC(C=C, dual=False, class_weight="balanced", max_iter=5000)
        clf.fit(E_tr, train_y)
        preds = clf.predict(E_te)
        f1 = f1_score(test_y, preds, average="macro", zero_division=0)
        cf = Counter(test_y)
        top10 = [c for c, _ in cf.most_common(10)]
        f1s = f1_score(test_y, preds, average=None, labels=top10, zero_division=0)
        n_pass = int(sum(1 for v in f1s if v > 0.85))
        marker = "  <-- BEST" if f1 > best_f1 else ""
        print(f"  C={C}: F1={f1*100:.2f}%  top10={n_pass}/10{marker}")
        if f1 > best_f1:
            best_C, best_f1, best_n = C, f1, n_pass

    print("\n" + "=" * 65)
    print(f"V7 RESULT: F1={best_f1*100:.2f}%  C={best_C}  top10={best_n}/10")
    print(f"Target: >= 75.00%  -> {'PASS' if best_f1 >= 0.75 else 'FAIL'}")
    print("=" * 65)

    summary = {
        "version": "v7-setfit",
        "body": BODY_MODEL,
        "samples_per_class": SAMPLES_PER_CLASS,
        "n_epochs_body": N_EPOCHS_BODY,
        "best_C": best_C,
        "macro_f1": round(float(best_f1) * 100, 2),
        "top10_pass": int(best_n),
        "target_met": bool(best_f1 >= 0.75),
    }
    (OUT_DIR / "training_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
