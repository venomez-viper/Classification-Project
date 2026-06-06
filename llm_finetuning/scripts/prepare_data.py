"""
Stage 1: Data preparation for LLM fine-tuning.

Reads the cleaned capstone CSVs, combines text columns the same way the
TF-IDF baseline did, encodes labels to 0-based integer indices, and writes
two ready-to-train CSVs plus label-map JSON files into llm_finetuning/data/.

Usage:
    python llm_finetuning/scripts/prepare_data.py
"""

import json
import os
import re

import pandas as pd
from sklearn.model_selection import train_test_split

# ── Paths ────────────────────────────────────────────────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CLEANED = os.path.join(ROOT, "data", "cleaned")
OUT_DIR = os.path.join(ROOT, "llm_finetuning", "data")
os.makedirs(OUT_DIR, exist_ok=True)

RANDOM_STATE = 42
TEST_SIZE = 0.2
MIN_SAMPLES_PER_CLASS = 2   # classes below this are dropped (can't stratify-split)


# ── Helpers ──────────────────────────────────────────────────────────────────
def clean_text(s: str) -> str:
    """Normalise whitespace and strip leading/trailing space."""
    s = str(s) if not isinstance(s, str) else s
    return re.sub(r"\s+", " ", s).strip()


def encode_labels(series: pd.Series):
    """Return (encoded int series, code->idx dict, idx->code dict)."""
    codes = sorted(series.unique().tolist())
    code_to_idx = {c: i for i, c in enumerate(codes)}
    idx_to_code = {i: c for c, i in code_to_idx.items()}
    return series.map(code_to_idx), code_to_idx, idx_to_code


def drop_rare_classes(df: pd.DataFrame, label_col: str, min_samples: int):
    counts = df[label_col].value_counts()
    valid = counts[counts >= min_samples].index
    before = len(df)
    df = df[df[label_col].isin(valid)].copy()
    dropped_classes = len(counts) - len(valid)
    dropped_rows = before - len(df)
    if dropped_classes:
        print(f"  Dropped {dropped_classes} classes with < {min_samples} samples "
              f"({dropped_rows} rows removed)")
    return df


def stratified_split(df: pd.DataFrame, label_col: str):
    train, test = train_test_split(
        df, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=df[label_col]
    )
    return train.reset_index(drop=True), test.reset_index(drop=True)


def save_artifacts(train, test, full, task_name, label_col, code_to_idx, idx_to_code):
    prefix = os.path.join(OUT_DIR, task_name)
    train.to_csv(f"{prefix}_train.csv", index=False)
    test.to_csv(f"{prefix}_test.csv", index=False)
    full.to_csv(f"{prefix}_full.csv", index=False)

    with open(f"{prefix}_code_to_idx.json", "w") as f:
        json.dump({str(k): v for k, v in code_to_idx.items()}, f, indent=2)
    with open(f"{prefix}_idx_to_code.json", "w") as f:
        json.dump({str(k): v for k, v in idx_to_code.items()}, f, indent=2)

    print(f"  Saved: {task_name}_train.csv  ({len(train)} rows)")
    print(f"  Saved: {task_name}_test.csv   ({len(test)} rows)")
    print(f"  Saved: {task_name}_full.csv   ({len(full)} rows)")
    print(f"  Saved: label maps (code_to_idx / idx_to_code)")


# ── Task 1: GECS Industry (145 classes) ─────────────────────────────────────
def prepare_task1():
    print("\n--- Task 1: GECS Industry Classification ---")
    df = pd.read_csv(os.path.join(CLEANED, "task1_clean.csv"))
    print(f"  Loaded {len(df)} rows, {df['MstarGlobal'].nunique()} classes")

    # Combine text exactly as the TF-IDF baseline did
    df["text"] = (
        df["LongProfile"].fillna("") + " "
        + df["SegmentName"].fillna("") + " "
        + df["SegmentDescription"].fillna("")
    ).apply(clean_text)

    df = drop_rare_classes(df, "MstarGlobal", MIN_SAMPLES_PER_CLASS)

    df["label_idx"], code_to_idx, idx_to_code = encode_labels(df["MstarGlobal"])
    df["mstar_code"] = df["MstarGlobal"]

    out = df[["text", "label_idx", "mstar_code"]].copy()

    train, test = stratified_split(out, "label_idx")
    save_artifacts(train, test, out, "task1", "label_idx", code_to_idx, idx_to_code)

    print(f"  Classes: {len(code_to_idx)}")
    print(f"  Avg text length (chars): {out['text'].str.len().mean():.0f}")
    print(f"  Avg text length (words): {out['text'].str.split().apply(len).mean():.0f}")


# ── Task 2: GECS Subindustry (428 classes) ───────────────────────────────────
def prepare_task2():
    print("\n--- Task 2: GECS Subindustry Classification ---")
    df = pd.read_csv(os.path.join(CLEANED, "task2_clean.csv"))
    print(f"  Loaded {len(df)} rows, {df['Subindustry'].nunique()} classes")

    # Task 2 has no LongProfile — use SegmentName + SegmentDescription
    df["text"] = (
        df["SegmentName"].fillna("") + " "
        + df["SegmentDescription"].fillna("")
    ).apply(clean_text)

    df = drop_rare_classes(df, "Subindustry", MIN_SAMPLES_PER_CLASS)

    df["label_idx"], code_to_idx, idx_to_code = encode_labels(df["Subindustry"])
    df["sub_code"] = df["Subindustry"]

    out = df[["text", "label_idx", "sub_code"]].copy()

    train, test = stratified_split(out, "label_idx")
    save_artifacts(train, test, out, "task2", "label_idx", code_to_idx, idx_to_code)

    print(f"  Classes: {len(code_to_idx)}")
    print(f"  Avg text length (chars): {out['text'].str.len().mean():.0f}")
    print(f"  Avg text length (words): {out['text'].str.split().apply(len).mean():.0f}")


# ── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("LLM Fine-Tuning — Stage 1: Data Preparation")
    print("=" * 60)

    prepare_task1()
    prepare_task2()

    print("\nDone. All files written to llm_finetuning/data/")
    print("Next: open llm_finetuning/notebooks/01_finetune_deberta.ipynb in Colab")
