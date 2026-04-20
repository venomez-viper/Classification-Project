# MGT 599 Capstone Project
## Group 4 — Industry and Subindustry Classification

Strayer University | April 2026

---

## Project Overview

This project builds a machine learning pipeline to automatically classify companies into industry and subindustry categories based on their text descriptions. The dataset contains company and segment-level records with revenue data and text profiles.

Two classification tasks are addressed:

- **Task 1** — Predict the industry label for a company using its long-form description
- **Task 2** — Predict the subindustry label for a business segment using its segment description

---

## Repository Structure

```
capstone MGT 599/
├── main.py                        # Run this first - loads, validates, cleans, exports data
├── .gitignore
├── README.md
│
├── data/
│   ├── loader.py                  # Loads raw CSVs into DuckDB
│   ├── cleaner.py                 # Cleans tables and exports to data/cleaned/
│   └── validator.py               # Validates row counts and schema
│
├── scripts/
│   ├── common_utils.py            # Shared utilities imported by all scripts
│   ├── lead_tracking.py           # Team tracker and documentation templates
│   ├── dashboard.py               # Descriptive analytics and charts
│   ├── task1_features.py          # Feature engineering for Task 1
│   ├── task2_features.py          # Feature engineering for Task 2
│   └── model_ready.py             # Final review and model-ready file export
│
├── notebooks/
│   ├── week2_submission.ipynb     # Complete Week 2 pipeline notebook
│   └── descriptive_analytics.ipynb
│
├── outputs/                       # Generated at runtime, not tracked by git
│   ├── dashboard/
│   ├── features/
│   │   ├── task1/
│   │   └── task2/
│   └── model_ready/
│
└── docs/
    ├── Week2_What_We_Did.md
    ├── weekly_reports/
    ├── findings_summary/
    └── handoff_notes/
```

---

## Setup

### Requirements

Python 3.10 or higher is recommended.

Install all required packages:

```
pip install pandas numpy matplotlib seaborn scikit-learn duckdb wordcloud jupyter
```

### Important note on data files

Raw data files and output CSVs are excluded from this repository via `.gitignore` because they are too large for GitHub. Each team member needs to have the raw data files placed in the `data/raw/` folder before running the pipeline.

If you pulled this repo fresh and do not have the raw data, contact the team lead to get the CSV files.

---

## How to Run the Pipeline

Run these commands from the project root directory (`capstone MGT 599/`).

**Step 1 — Run the main pipeline first**

This loads the raw data, cleans it, and exports cleaned CSVs to `data/cleaned/`.

```
python main.py
```

This must be completed before any other script will work.

**Step 2 — Run the team scripts (can be run in parallel)**

From inside the `scripts/` folder:

```
cd scripts
python lead_tracking.py
python dashboard.py
python task1_features.py
python task2_features.py
```

**Step 3 — Run model_ready.py last**

Only after task1_features.py and task2_features.py have finished:

```
python model_ready.py
```

**Notebooks**

Open Jupyter Lab from the project root and run either notebook top to bottom:

```
jupyter lab
```

---

## How to Commit and Push Your Work

Follow these steps every time you finish your section and want to save your work to the shared repo.

**1. Check what files you changed**

```
git status
```

**2. Stage your changes**

To stage everything:
```
git add .
```

Or to stage a specific file:
```
git add scripts/dashboard.py
```

**3. Commit with a clear message describing what you did**

```
git commit -m "dashboard - added class distribution charts and missing value summary"
```

Keep commit messages short and specific. Bad example: `updated stuff`. Good example: `task1 features - added tfidf on combined text columns`.

**4. Pull before you push to avoid conflicts**

```
git pull origin main
```

**5. Push your changes**

```
git push origin main
```

---

## Workflow Rules for the Team

- Always run `git pull origin main` before starting work each session.
- Each person works in their own script — do not edit another person's script without discussing first.
- Do not commit large CSV files, raw data, or output files. The `.gitignore` already handles this.
- If you get a merge conflict, do not force push. Contact the team lead to resolve it.
- Write a brief handoff note in `docs/handoff_notes/` when you finish a section.

---

## Output Files Reference

After running the full pipeline, the following files will exist locally:

| File | Location | Created by |
|------|----------|------------|
| task1_clean.csv | data/cleaned/ | main.py |
| task2_clean.csv | data/cleaned/ | main.py |
| task1_features_full_v1.csv | outputs/features/task1/ | task1_features.py |
| task2_features_full_v1.csv | outputs/features/task2/ | task2_features.py |
| task1_model_ready_v1.csv | outputs/model_ready/ | model_ready.py |
| task2_model_ready_v1.csv | outputs/model_ready/ | model_ready.py |

---

## Week Status

| Week | Focus | Status |
|------|-------|--------|
| Week 1 | Project setup, EDA, data understanding | Complete |
| Week 2 | Data cleaning, feature engineering, descriptive analytics | Complete |
| Week 3 | Baseline model training and evaluation | Upcoming |
| Week 4 | Model refinement and final report | Upcoming |

---

MGT 599 Capstone — Group 4
