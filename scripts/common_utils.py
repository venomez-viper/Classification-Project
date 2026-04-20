# common_utils.py
# Shared helper functions used by all team scripts
# Don't run this file directly - just import from it

from pathlib import Path
import re
import pandas as pd
import seaborn as sns


# Change this if your project folder is somewhere else
BASE_PATH = Path(r"C:\Users\akash\Desktop\capstone MGT 599")

DATA_PATH        = BASE_PATH / "data"
CLEANED_PATH     = DATA_PATH / "cleaned"
OUTPUT_PATH      = BASE_PATH / "outputs"
DOCS_PATH        = BASE_PATH / "docs"

DASHBOARD_PATH       = OUTPUT_PATH / "dashboard"
FIGURES_PATH         = OUTPUT_PATH / "figures"
TASK1_FEATURE_PATH   = OUTPUT_PATH / "features" / "task1"
TASK2_FEATURE_PATH   = OUTPUT_PATH / "features" / "task2"
MODEL_READY_PATH     = OUTPUT_PATH / "model_ready"
WEEKLY_REPORT_PATH   = DOCS_PATH / "weekly_reports"
FINDINGS_PATH        = DOCS_PATH / "findings_summary"
HANDOFF_PATH         = DOCS_PATH / "handoff_notes"


def ensure_folders():
    # make sure every folder we need actually exists
    folders = [
        DATA_PATH, CLEANED_PATH, OUTPUT_PATH, DOCS_PATH,
        DASHBOARD_PATH, FIGURES_PATH,
        TASK1_FEATURE_PATH, TASK2_FEATURE_PATH,
        MODEL_READY_PATH, WEEKLY_REPORT_PATH,
        FINDINGS_PATH, HANDOFF_PATH,
    ]
    for f in folders:
        f.mkdir(parents=True, exist_ok=True)


def find_dataset(task_name):
    """Look for the cleaned CSV for task1 or task2 in data/cleaned/"""
    task_name = task_name.lower().strip()

    if task_name == "task1":
        patterns = ["*task1*clean*.csv", "*task1*.csv", "*gecs*clean*.csv"]
    elif task_name == "task2":
        patterns = ["*task2*clean*.csv", "*task2*.csv", "*subindustry*clean*.csv"]
    else:
        raise ValueError("task_name has to be 'task1' or 'task2'")

    found = []
    for pat in patterns:
        found.extend(CLEANED_PATH.glob(pat))
    found = sorted(set(found))

    if not found:
        available = [p.name for p in CLEANED_PATH.glob("*.csv")]
        raise FileNotFoundError(
            f"No cleaned CSV found for {task_name} in {CLEANED_PATH}\n"
            f"Files available: {available}\n"
            f"TIP: Run main.py first to export cleaned data from DuckDB to data/cleaned/"
        )
    return found[0]


def load_task_dataframe(task_name):
    """Load a task CSV and print basic info"""
    path = find_dataset(task_name)
    print(f"Loading {task_name} from: {path}")
    df = pd.read_csv(path)
    print(f"Loaded! Shape: {df.shape}")
    return df


def print_basic_info(df, name):
    print(f"\n--- {name} overview ---")
    print(f"Rows x Cols: {df.shape}")
    print("Columns:", list(df.columns))


def guess_target_column(df, task_name):
    """Try to figure out which column is the label we're predicting"""
    col_map = {c.lower().replace(" ", "").replace("_", ""): c for c in df.columns}
    task_name = task_name.lower().strip()

    if task_name == "task1":
        guesses = ["mstarglobal", "industry", "gecsindustry", "industrymstarglobal"]
    else:
        guesses = ["subindustry", "businessactivity", "activity", "subindustry"]

    for g in guesses:
        if g in col_map:
            print(f"Guessed target column for {task_name}: {col_map[g]}")
            return col_map[g]

    # last resort - find anything with 'industry' or 'activity' in name
    keywords = ["industry"] if task_name == "task1" else ["sub", "activity"]
    for k, v in col_map.items():
        if any(kw in k for kw in keywords):
            return v

    raise ValueError(
        f"Couldn't figure out target column for {task_name}. "
        f"Set it manually. Columns are: {list(df.columns)}"
    )


def guess_text_columns(df):
    """Pick text columns in a reasonable priority order"""
    priority = [
        "longprofile", "companydescription", "longformdescription",
        "segmentdescription", "segmentname", "description",
    ]
    col_map = {c.lower().replace(" ", "").replace("_", ""): c for c in df.columns}
    result = []
    seen = set()
    for p in priority:
        if p in col_map and col_map[p] not in seen:
            result.append(col_map[p])
            seen.add(col_map[p])
    return result


def safe_text(series):
    """Fill NaN with empty string and cast to str"""
    return series.fillna("").astype(str)


def add_basic_text_features(df, text_columns):
    """Add simple text stats for each column: length, word count, etc."""
    for col in text_columns:
        if col not in df.columns:
            print(f"  skipping {col} - not found")
            continue
        txt = safe_text(df[col])
        df[f"{col}_char_len"]         = txt.apply(len)
        df[f"{col}_word_count"]       = txt.apply(lambda x: len(x.split()))
        df[f"{col}_unique_word_count"]= txt.apply(lambda x: len(set(x.split())))
        df[f"{col}_avg_word_len"]     = txt.apply(
            lambda x: round(sum(len(w) for w in x.split()) / len(x.split()), 2)
            if x.split() else 0
        )
        df[f"{col}_has_text"] = txt.apply(lambda x: 1 if x.strip() else 0)
    return df


def add_keyword_features(df, source_column, keywords, prefix="kw"):
    """Add a 0/1 column for each keyword - did it appear in the text?"""
    if source_column not in df.columns:
        print(f"  column not found: {source_column}")
        return df
    txt = safe_text(df[source_column]).str.lower()
    for word in keywords:
        col_name = re.sub(r"[^a-zA-Z0-9]+", "_", word.lower()).strip("_")
        df[f"{prefix}_{col_name}"] = txt.str.contains(re.escape(word.lower()), na=False).astype(int)
    return df


def create_summary_table(df, target_col, dataset_name):
    return pd.DataFrame({
        "dataset_name"        : [dataset_name],
        "row_count"           : [df.shape[0]],
        "column_count"        : [df.shape[1]],
        "target_column"       : [target_col],
        "unique_target_labels": [df[target_col].nunique() if target_col in df.columns else None],
    })


def save_markdown_report(path, title, body_lines):
    lines = [f"# {title}", ""] + body_lines
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Saved: {path}")


def simple_missing_summary(df):
    return pd.DataFrame({
        "column"         : df.columns,
        "missing_count"  : [df[c].isna().sum() for c in df.columns],
        "missing_percent": [round(df[c].isna().mean() * 100, 2) for c in df.columns],
    }).sort_values("missing_count", ascending=False)


def save_dataframe(df, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    print(f"Saved: {path}")


# more helpers added in week 2

def set_chart_style():
    import matplotlib.pyplot as plt
    sns.set_style("whitegrid")
    plt.rcParams["figure.figsize"] = (10, 6)
    plt.rcParams["figure.dpi"] = 120


def combine_text_fields(df, columns, new_col="combined_text"):
    # stick multiple text columns together into one big string
    parts = [safe_text(df[c]) for c in columns if c in df.columns]
    if not parts:
        return df
    combined = parts[0]
    for p in parts[1:]:
        combined = combined + " " + p
    df[new_col] = combined.str.strip()
    return df


def find_weak_features(df, threshold=0.99):
    # columns where almost every row has the same value - not useful for a model
    weak = []
    for col in df.select_dtypes(include=["number"]).columns:
        if df[col].dropna().empty:
            continue
        top_pct = df[col].value_counts(normalize=True).iloc[0]
        if top_pct >= threshold:
            weak.append((col, round(top_pct * 100, 1)))
    return weak


def analyze_imbalance(series, name="target"):
    counts = series.value_counts()
    total = len(series)
    top3 = counts.head(3).sum() / total * 100
    rare = int((counts < 10).sum())
    print(f"\n{name} label breakdown:")
    print(f"  unique classes: {len(counts)}")
    print(f"  top 3 cover: {top3:.1f}%")
    print(f"  classes with < 10 rows: {rare}")
    return {"unique": len(counts), "top3_pct": round(top3, 1), "rare_classes": rare}
