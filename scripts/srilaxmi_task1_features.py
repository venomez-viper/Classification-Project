# srilaxmi_task1_features.py
# Task 1 feature engineering - Industry classification
# Reads from data/cleaned/, writes to outputs/features/task1/
# Run at the same time as Tserennad and Vishal - no conflicts
# Usage: python srilaxmi_task1_features.py

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

from common_utils import (
    TASK1_FEATURE_PATH,
    FINDINGS_PATH,
    ensure_folders,
    load_task_dataframe,
    guess_target_column,
    guess_text_columns,
    add_basic_text_features,
    add_keyword_features,
    save_dataframe,
    save_markdown_report,
    safe_text,
    combine_text_fields,
)


def pick_main_text_col(df, text_cols):
    """Pick the best column to run TF-IDF on.
    Prefers a company-level description over segment-level."""
    preference = [
        "LongProfile", "CompanyDescription", "LongFormDescription",
        "SegmentDescription", "Segment Description",
    ]
    for p in preference:
        if p in df.columns:
            return p
    if text_cols:
        return text_cols[0]
    raise ValueError("No text column found. Check column names.")


def main():
    ensure_folders()
    print("=== Srilaxmi Task 1 Feature Engineering ===\n")

    task1 = load_task_dataframe("task1")
    target_col  = guess_target_column(task1, "task1")
    text_cols   = guess_text_columns(task1)

    print(f"Target column : {target_col}")
    print(f"Text columns  : {text_cols}")

    # Step 1 - basic text stats (length, word count, etc.)
    task1 = add_basic_text_features(task1, text_cols)

    # Step 2 - pick main text column for TF-IDF
    main_col = pick_main_text_col(task1, text_cols)
    print(f"Using '{main_col}' for main TF-IDF")

    # flag rows where the description is really short (less than 5 words)
    task1["short_desc_flag"] = (
        safe_text(task1[main_col]).str.split().str.len() < 5
    ).astype(int)
    print(f"Short descriptions (< 5 words): {task1['short_desc_flag'].sum()}")

    # Step 3 - keyword features that relate to industry categories
    industry_keywords = [
        "bank", "finance", "financial", "insurance", "retail",
        "software", "technology", "healthcare", "medical", "pharma",
        "energy", "oil", "gas", "manufacturing", "industrial",
        "telecom", "transport", "logistics",
    ]
    task1 = add_keyword_features(task1, main_col, industry_keywords, prefix="industry_kw")

    # Step 4 - TF-IDF on the main text column
    print("Building TF-IDF on main text column...")
    tfidf_vec = TfidfVectorizer(max_features=300, stop_words="english", ngram_range=(1, 2))
    X_tfidf   = tfidf_vec.fit_transform(safe_text(task1[main_col]))
    tfidf_df  = pd.DataFrame(
        X_tfidf.toarray(),
        columns=[f"tfidf_{n}" for n in tfidf_vec.get_feature_names_out()]
    )

    # Step 5 - TF-IDF on combined text (all text columns stuck together)
    print("Building TF-IDF on combined text...")
    task1 = combine_text_fields(task1, text_cols, "combined_text")
    comb_vec = TfidfVectorizer(max_features=300, stop_words="english", ngram_range=(1, 2))
    X_comb   = comb_vec.fit_transform(safe_text(task1["combined_text"]))
    comb_df  = pd.DataFrame(
        X_comb.toarray(),
        columns=[f"comb_tfidf_{n}" for n in comb_vec.get_feature_names_out()]
    )

    # save files
    basic_file  = TASK1_FEATURE_PATH / "task1_features_basic_v1.csv"
    tfidf_file  = TASK1_FEATURE_PATH / "task1_tfidf_features_v1.csv"
    full_file   = TASK1_FEATURE_PATH / "task1_features_full_v1.csv"
    comb_file   = TASK1_FEATURE_PATH / "task1_combined_tfidf_v1.csv"

    save_dataframe(task1, basic_file)
    save_dataframe(tfidf_df, tfidf_file)
    save_dataframe(comb_df, comb_file)

    full_df = pd.concat([task1.reset_index(drop=True), tfidf_df.reset_index(drop=True)], axis=1)
    save_dataframe(full_df, full_file)

    # summary report
    body = [
        "## Objective",
        "- Build features for Task 1 industry classification.",
        "",
        "## Files created",
        f"- `{basic_file.name}` - original data + text stats + keyword flags",
        f"- `{tfidf_file.name}` - TF-IDF on main text column (300 features)",
        f"- `{comb_file.name}` - TF-IDF on all text columns combined (300 features)",
        f"- `{full_file.name}` - everything merged into one file",
        "",
        "## What was done",
        f"- Target column used: **{target_col}**",
        f"- Main TF-IDF column: **{main_col}**",
        f"- Text columns processed: {text_cols}",
        f"- Short description rows flagged: **{int(task1['short_desc_flag'].sum())}**",
        f"- Keyword features added: **{len(industry_keywords)}**",
        f"- TF-IDF features: **{tfidf_df.shape[1]}** (single) + **{comb_df.shape[1]}** (combined)",
        f"- Full feature file shape: **{full_df.shape}**",
        "",
        "## Next step",
        "- Tell Subasree: Task 1 features are ready in outputs/features/task1/",
    ]
    save_markdown_report(FINDINGS_PATH / "task1_feature_summary.md", "Task 1 Feature Engineering Summary", body)

    print("\nTask 1 feature engineering completed successfully.")


if __name__ == "__main__":
    main()
