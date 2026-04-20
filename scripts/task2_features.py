# task2_features.py
# Task 2 feature engineering - Business Activity / Subindustry classification
# Reads from data/cleaned/, writes to outputs/features/task2/
# Run at the same time as dashboard.py and task1_features.py - no conflicts
# Usage: python task2_features.py

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

from common_utils import (
    TASK2_FEATURE_PATH,
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
    """Pick the best column to run TF-IDF on for Task 2.
    Prefers segment-level description since task2 is segment-focused."""
    preference = [
        "SegmentDescription", "Segment Description",
        "SegmentName", "Segment Name",
        "LongProfile", "CompanyDescription",
    ]
    for p in preference:
        if p in df.columns:
            return p
    if text_cols:
        return text_cols[0]
    raise ValueError("No text column found for Task 2. Check column names.")


def main():
    ensure_folders()
    print("task 2 feature engineering starting...\n")

    task2 = load_task_dataframe("task2")
    target_col = guess_target_column(task2, "task2")
    text_cols  = guess_text_columns(task2)

    print(f"Target column : {target_col}")
    print(f"Text columns  : {text_cols}")

    # Step 1 - basic text stats
    task2 = add_basic_text_features(task2, text_cols)

    # Step 2 - pick main text column
    main_col = pick_main_text_col(task2, text_cols)
    print(f"Using '{main_col}' for main TF-IDF")

    # flag short descriptions
    task2["short_desc_flag"] = (
        safe_text(task2[main_col]).str.split().str.len() < 5
    ).astype(int)
    print(f"Short descriptions (< 5 words): {task2['short_desc_flag'].sum()}")

    # Step 3 - keyword features for business activity types
    activity_keywords = [
        "delivery", "transport", "logistics", "cloud", "platform",
        "payments", "medical", "device", "manufacturing", "processing",
        "software", "retail", "distribution", "construction", "consulting",
        "analytics", "security", "energy", "packaging", "warehousing",
        "saas", "subscription", "staffing", "outsourcing", "brokerage", "leasing",
    ]
    task2 = add_keyword_features(task2, main_col, activity_keywords, prefix="activity_kw")

    # Step 4 - TF-IDF on main text column
    print("Building TF-IDF on main text column...")
    tfidf_vec = TfidfVectorizer(max_features=300, stop_words="english", ngram_range=(1, 2))
    X_tfidf   = tfidf_vec.fit_transform(safe_text(task2[main_col]))
    tfidf_df  = pd.DataFrame(
        X_tfidf.toarray(),
        columns=[f"tfidf_{n}" for n in tfidf_vec.get_feature_names_out()]
    )

    # Step 5 - TF-IDF on combined text
    print("Building TF-IDF on combined text...")
    task2 = combine_text_fields(task2, text_cols, "combined_text")
    comb_vec = TfidfVectorizer(max_features=300, stop_words="english", ngram_range=(1, 2))
    X_comb   = comb_vec.fit_transform(safe_text(task2["combined_text"]))
    comb_df  = pd.DataFrame(
        X_comb.toarray(),
        columns=[f"comb_tfidf_{n}" for n in comb_vec.get_feature_names_out()]
    )

    # save files
    basic_file = TASK2_FEATURE_PATH / "task2_features_basic_v1.csv"
    tfidf_file = TASK2_FEATURE_PATH / "task2_tfidf_features_v1.csv"
    full_file  = TASK2_FEATURE_PATH / "task2_features_full_v1.csv"
    comb_file  = TASK2_FEATURE_PATH / "task2_combined_tfidf_v1.csv"

    save_dataframe(task2, basic_file)
    save_dataframe(tfidf_df, tfidf_file)
    save_dataframe(comb_df, comb_file)

    full_df = pd.concat([task2.reset_index(drop=True), tfidf_df.reset_index(drop=True)], axis=1)
    save_dataframe(full_df, full_file)

    body = [
        "## Objective",
        "- Build features for Task 2 business activity / subindustry classification.",
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
        f"- Short description rows flagged: **{int(task2['short_desc_flag'].sum())}**",
        f"- Keyword features added: **{len(activity_keywords)}**",
        f"- TF-IDF features: **{tfidf_df.shape[1]}** (single) + **{comb_df.shape[1]}** (combined)",
        f"- Full feature file shape: **{full_df.shape}**",
        "",
        "## Next step",
        "- Task 2 features are ready in outputs/features/task2/ - notify whoever is running model_ready.py",
    ]
    save_markdown_report(FINDINGS_PATH / "task2_feature_summary.md", "Task 2 Feature Engineering Summary", body)

    print("\ntask 2 done.")


if __name__ == "__main__":
    main()
