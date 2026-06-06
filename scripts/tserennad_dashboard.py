# tserennad_dashboard.py
# Descriptive analytics and dashboard charts
# Reads from data/cleaned/ and writes to outputs/dashboard/
# Run at the same time as Srilaxmi and Vishal - no conflicts
# Usage: python tserennad_dashboard.py

import matplotlib.pyplot as plt
import pandas as pd

from common_utils import (
    DASHBOARD_PATH,
    FINDINGS_PATH,
    ensure_folders,
    guess_target_column,
    guess_text_columns,
    load_task_dataframe,
    print_basic_info,
    create_summary_table,
    save_dataframe,
    save_markdown_report,
    simple_missing_summary,
    safe_text,
    set_chart_style,
    analyze_imbalance,
)

set_chart_style()


def save_bar_chart(series, title, xlabel, ylabel, output_name):
    """Basic vertical bar chart"""
    fig, ax = plt.subplots()
    series.plot(kind="bar", ax=ax, color="#2E75B6")
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    out = DASHBOARD_PATH / output_name
    plt.savefig(out, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"  Saved chart: {out.name}")


def save_horizontal_bar(series, title, output_name):
    """Horizontal bar chart - easier to read long class names"""
    fig, ax = plt.subplots(figsize=(12, 7))
    series.plot(kind="barh", ax=ax, color="#2E75B6")
    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xlabel("Count")
    ax.invert_yaxis()
    # add count labels at the end of each bar
    for i, v in enumerate(series.values):
        ax.text(v + max(series) * 0.01, i, str(v), va="center", fontsize=9)
    plt.tight_layout()
    plt.savefig(DASHBOARD_PATH / output_name, bbox_inches="tight", dpi=200)
    plt.close()
    print(f"  Saved chart: {output_name}")


def save_histogram(series, title, xlabel, ylabel, output_name):
    """Save a histogram"""
    fig, ax = plt.subplots()
    series.hist(bins=30, ax=ax, color="#4472C4", edgecolor="white")
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    plt.tight_layout()
    out = DASHBOARD_PATH / output_name
    plt.savefig(out, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"  Saved chart: {out.name}")


def analyze_text_lengths(df, label, text_columns):
    """Create text-length charts and return a list of findings"""
    findings = []
    for col in text_columns:
        if col not in df.columns:
            continue
        txt       = safe_text(df[col])
        char_lens = txt.apply(len)
        word_cnts = txt.apply(lambda x: len(x.split()))

        safe_col = col.replace(" ", "_").lower()
        save_histogram(
            char_lens,
            title=f"{label}: character length in {col}",
            xlabel="Length (chars)", ylabel="Count",
            output_name=f"{label.lower()}_{safe_col}_char_hist.png",
        )
        save_histogram(
            word_cnts,
            title=f"{label}: word count in {col}",
            xlabel="Word count", ylabel="Count",
            output_name=f"{label.lower()}_{safe_col}_word_hist.png",
        )
        findings.append(
            f"- **{label}** / **{col}**: avg {round(char_lens.mean(),1)} chars, "
            f"avg {round(word_cnts.mean(),1)} words per row."
        )
    return findings


def main():
    ensure_folders()
    print("=== Tserennad Dashboard ===\n")

    task1 = load_task_dataframe("task1")
    task2 = load_task_dataframe("task2")

    print_basic_info(task1, "Task 1")
    print_basic_info(task2, "Task 2")

    task1_target   = guess_target_column(task1, "task1")
    task2_target   = guess_target_column(task2, "task2")
    task1_text_cols = guess_text_columns(task1)
    task2_text_cols = guess_text_columns(task2)

    # dataset summary table
    summary = pd.concat([
        create_summary_table(task1, task1_target, "Task 1"),
        create_summary_table(task2, task2_target, "Task 2"),
    ], ignore_index=True)
    save_dataframe(summary, DASHBOARD_PATH / "dataset_summary.csv")

    # missing value summaries
    save_dataframe(simple_missing_summary(task1), DASHBOARD_PATH / "task1_missing_summary.csv")
    save_dataframe(simple_missing_summary(task2), DASHBOARD_PATH / "task2_missing_summary.csv")

    # top class bar charts
    t1_top = task1[task1_target].value_counts().head(10)
    t2_top = task2[task2_target].value_counts().head(10)

    save_bar_chart(t1_top,
        title="Top 10 Industry Classes (Task 1)",
        xlabel=task1_target, ylabel="Count",
        output_name="task1_top10_industry_classes.png")

    save_bar_chart(t2_top,
        title="Top 10 Business Activity Classes (Task 2)",
        xlabel=task2_target, ylabel="Count",
        output_name="task2_top10_activity_classes.png")

    # horizontal bar versions (easier to read)
    save_horizontal_bar(t1_top, "Top 10 Industry Classes (Task 1)", "task1_top10_industry_barh.png")
    save_horizontal_bar(t2_top, "Top 10 Activity Classes (Task 2)", "task2_top10_activity_barh.png")

    # class imbalance analysis
    t1_imb = analyze_imbalance(task1[task1_target], "Task 1")
    t2_imb = analyze_imbalance(task2[task2_target], "Task 2")

    # text length charts and findings
    t1_findings = analyze_text_lengths(task1, "Task1", task1_text_cols)
    t2_findings = analyze_text_lengths(task2, "Task2", task2_text_cols)

    # word cloud for top text column if wordcloud is installed
    try:
        from wordcloud import WordCloud
        for col in task1_text_cols[:1]:
            text_joined = " ".join(safe_text(task1[col]))
            wc = WordCloud(
                width=900, height=400,
                background_color="white", max_words=100,
                colormap="Blues", collocations=False
            ).generate(text_joined)
            plt.figure(figsize=(14, 7))
            plt.imshow(wc, interpolation="bilinear")
            plt.axis("off")
            plt.title(f"Most Common Words in {col}", fontsize=14)
            out = DASHBOARD_PATH / f"wordcloud_{col.replace(' ','_').lower()}.png"
            plt.savefig(out, bbox_inches="tight", dpi=150)
            plt.close()
            print(f"  Saved word cloud: {out.name}")
    except ImportError:
        print("  wordcloud not installed, skipping. Run: pip install wordcloud")

    # write the markdown summary
    body = [
        "## What was analyzed",
        "- Loaded both cleaned datasets.",
        "- Created dataset summary tables.",
        "- Checked missing values for both tasks.",
        "- Made top-10 class distribution charts.",
        "- Made text-length histograms for key text columns.",
        "",
        "## Main observations",
        f"- Task 1 target column: **{task1_target}**  |  unique labels: **{task1[task1_target].nunique()}**",
        f"- Task 2 target column: **{task2_target}**  |  unique labels: **{task2[task2_target].nunique()}**",
        f"- Task 1 top 3 classes cover **{t1_imb['top3_pct']}%** of all records.",
        f"- Task 2 top 3 classes cover **{t2_imb['top3_pct']}%** of all records.",
        f"- Task 1 classes with fewer than 10 records: **{t1_imb['rare_classes']}**.",
        f"- Task 2 classes with fewer than 10 records: **{t2_imb['rare_classes']}**.",
        *t1_findings,
        *t2_findings,
        "",
        "## Recommended next step",
        "- Use text fields and class distribution info to guide feature engineering (Srilaxmi and Vishal).",
    ]
    save_markdown_report(FINDINGS_PATH / "dashboard_findings_summary.md", "Dashboard Findings Summary", body)

    print("\nDashboard work completed successfully.")


if __name__ == "__main__":
    main()
