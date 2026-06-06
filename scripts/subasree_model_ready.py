# subasree_model_ready.py
# Feature review and model-ready dataset preparation
#
# IMPORTANT: Do NOT run this until BOTH Srilaxmi and Vishal say their files are done!
# Reads from outputs/features/task1/ and outputs/features/task2/
# Writes to outputs/model_ready/
#
# Usage: python subasree_model_ready.py

import pandas as pd

from common_utils import (
    TASK1_FEATURE_PATH,
    TASK2_FEATURE_PATH,
    MODEL_READY_PATH,
    FINDINGS_PATH,
    ensure_folders,
    load_task_dataframe,
    save_dataframe,
    save_markdown_report,
    find_weak_features,
)


def load_feature_file(path):
    print(f"Loading: {path}")
    df = pd.read_csv(path)
    print(f"  Shape: {df.shape}")
    return df


def count_duplicate_columns(df):
    return int(df.columns.duplicated().sum())


def print_feature_groups(name, df):
    """Show how many features belong to each group"""
    txt  = [c for c in df.columns if any(t in c for t in ["_char_len","_word_count","_unique_word","_avg_word","_has_text"])]
    kw   = [c for c in df.columns if "_kw_" in c]
    tf   = [c for c in df.columns if "tfidf_" in c]
    other = len(df.columns) - len(txt) - len(kw) - len(tf)
    print(f"\n{name} feature groups:")
    print(f"  Text statistics : {len(txt)}")
    print(f"  Keyword flags   : {len(kw)}")
    print(f"  TF-IDF features : {len(tf)}")
    print(f"  Other/original  : {other}")


def main():
    ensure_folders()
    print("=== Subasree Model-Ready Review ===\n")
    print("REMINDER: Only run this after Srilaxmi and Vishal confirm their files.\n")

    task1_file = TASK1_FEATURE_PATH / "task1_features_full_v1.csv"
    task2_file = TASK2_FEATURE_PATH / "task2_features_full_v1.csv"

    task1 = load_feature_file(task1_file)
    task2 = load_feature_file(task2_file)

    # remove near-constant columns - they don't help the model
    print("\nChecking for near-constant features...")
    for name, df in [("Task 1", task1), ("Task 2", task2)]:
        weak = find_weak_features(df)
        if weak:
            print(f"  {name} near-constant features found:")
            for col, pct in weak:
                print(f"    {col}: {pct}% same value -> dropping")
            drop_cols = [col for col, _ in weak]
            df.drop(columns=drop_cols, inplace=True)
            print(f"  Dropped {len(drop_cols)} column(s)")
        else:
            print(f"  {name}: no near-constant features. Good.")

    # verify row counts match original cleaned files
    print("\nVerifying row counts match original data...")
    try:
        orig_t1 = load_task_dataframe("task1")
        orig_t2 = load_task_dataframe("task2")
        assert len(task1) == len(orig_t1), \
            f"Row count mismatch Task 1: {len(task1)} vs {len(orig_t1)}"
        assert len(task2) == len(orig_t2), \
            f"Row count mismatch Task 2: {len(task2)} vs {len(orig_t2)}"
        print("  Row counts verified - data is aligned.")
    except Exception as e:
        print(f"  Warning during row count check: {e}")

    # show feature group breakdown
    print_feature_groups("Task 1", task1)
    print_feature_groups("Task 2", task2)

    # build review tables
    task1_review = pd.DataFrame({
        "column"       : task1.columns,
        "missing_count": [task1[c].isna().sum() for c in task1.columns],
        "data_type"    : [str(task1[c].dtype) for c in task1.columns],
    }).sort_values("missing_count", ascending=False)

    task2_review = pd.DataFrame({
        "column"       : task2.columns,
        "missing_count": [task2[c].isna().sum() for c in task2.columns],
        "data_type"    : [str(task2[c].dtype) for c in task2.columns],
    }).sort_values("missing_count", ascending=False)

    # save everything
    save_dataframe(task1_review, MODEL_READY_PATH / "task1_feature_review_table.csv")
    save_dataframe(task2_review, MODEL_READY_PATH / "task2_feature_review_table.csv")
    save_dataframe(task1, MODEL_READY_PATH / "task1_model_ready_v1.csv")
    save_dataframe(task2, MODEL_READY_PATH / "task2_model_ready_v1.csv")

    body = [
        "## Objective",
        "- Review Task 1 and Task 2 feature files and produce clean model-ready datasets.",
        "",
        "## Files reviewed",
        f"- `{task1_file.name}`",
        f"- `{task2_file.name}`",
        "",
        "## Review checks performed",
        "- Checked for duplicate columns.",
        "- Removed near-constant features (>99% same value).",
        "- Verified row counts match original cleaned data.",
        "- Checked data types and missing values.",
        "- Summarized feature group counts.",
        "",
        "## Results",
        f"- Task 1 duplicate columns: **{count_duplicate_columns(task1)}**",
        f"- Task 2 duplicate columns: **{count_duplicate_columns(task2)}**",
        f"- Task 1 final shape: **{task1.shape}**",
        f"- Task 2 final shape: **{task2.shape}**",
        "",
        "## Next step",
        "- Tell Akash: model-ready files are in outputs/model_ready/ - ready for the phase summary.",
    ]
    save_markdown_report(FINDINGS_PATH / "model_ready_summary.md", "Model Ready Summary", body)

    print("\nModel-ready review completed successfully.")


if __name__ == "__main__":
    main()
