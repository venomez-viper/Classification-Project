"""Generate the 6 ready-to-run Colab notebooks.

These notebooks are designed for parallel launch: open all six in separate
Colab tabs, choose a GPU runtime in each, run all cells, upload the requested
CSV files when prompted, then download the named top-k files for ensembling.
"""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
COLAB_DIR = ROOT / "colab"
NB_OUT = COLAB_DIR / "notebooks"
NB_OUT.mkdir(exist_ok=True)

T1_SCRIPT = (COLAB_DIR / "v3_train_flexible.py").read_text(encoding="utf-8")
T2_SCRIPT = (COLAB_DIR / "v3_task2_train.py").read_text(encoding="utf-8")


def make_cell(source: str, cell_type: str = "code"):
    lines = source.splitlines(keepends=True)
    if cell_type == "markdown":
        return {"cell_type": "markdown", "metadata": {}, "source": lines}
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": lines,
    }


def make_notebook(cells):
    return {
        "cells": cells,
        "metadata": {
            "accelerator": "GPU",
            "colab": {"gpuType": "A100", "provenance": []},
            "kernelspec": {"display_name": "Python 3", "name": "python3"},
            "language_info": {"name": "python"},
        },
        "nbformat": 4,
        "nbformat_minor": 0,
    }


def replace_config(script: str, new_config: dict, var_name: str = "CONFIG") -> str:
    lines = script.splitlines()
    start = None
    end = None
    for i, line in enumerate(lines):
        if line.strip().startswith(f"{var_name} = {{"):
            start = i
            depth = line.count("{") - line.count("}")
            j = i
            while depth > 0 and j + 1 < len(lines):
                j += 1
                depth += lines[j].count("{") - lines[j].count("}")
            end = j
            break
    if start is None or end is None:
        raise ValueError(f"Could not find {var_name} block")

    config_text = json.dumps(new_config, indent=4)
    config_text = config_text.replace("true", "True").replace("false", "False").replace("null", "None")
    return "\n".join(lines[:start] + [f"{var_name} = {config_text}"] + lines[end + 1 :])


def upload_cell(nb):
    expected = "\\n  - ".join(nb["upload_files"])
    path_prints = "\n".join(f"print(r'  {p}')" for p in nb["upload_paths"])
    return make_cell(
        f"""from google.colab import files
print("Upload exactly these files for {nb['run_label']}:\\n  - {expected}")
print("\\nWindows source paths:")
{path_prints}
uploaded = files.upload()
print("\\nUploaded:", list(uploaded.keys()))
"""
    )


def verify_cell(nb):
    checks = "\n".join(
        f'print("{name}:", "OK" if os.path.exists("/content/{name}") else "MISSING")'
        for name in nb["expected_files"]
    )
    missing_list = ", ".join(f'"{name}"' for name in nb["expected_files"])
    return make_cell(
        f"""import os
print("Verifying required files in /content for {nb['run_label']} ...")
{checks}
missing = [name for name in [{missing_list}] if not os.path.exists("/content/" + name)]
if missing:
    raise FileNotFoundError("Missing required uploads: " + ", ".join(missing))
"""
    )


def header_cell(nb):
    upload_lines = "\n".join(f"- `{name}`" for name in nb["upload_files"])
    path_lines = "\n".join(f"- `{path}`" for path in nb["upload_paths"])
    output_lines = "\n".join(f"- `{name}`" for name in nb["expected_outputs"])
    return make_cell(
        f"""# {nb['title']}

**Run label:** `{nb['run_label']}`  
**Run name:** `{nb['config']['RUN_NAME']}`  
**Track:** `{nb['track']}`  
**Ensemble role:** {nb['role']}

## Parallel launch steps
1. Open this notebook in its own Colab tab.
2. Set `Runtime -> Change runtime type -> GPU` and pick A100/L4/T4, whichever Pro+ gives you.
3. Click `Runtime -> Run all`.
4. Upload only the files listed below when the upload prompt appears.
5. Leave this tab running while you start the other five notebooks.
6. When it finishes, download the top-k file using the local filename shown at the bottom.

## Files to upload
{upload_lines}

## Windows paths
{path_lines}

## Expected Drive outputs
{output_lines}
""",
        cell_type="markdown",
    )


def finish_cell(nb):
    return make_cell(
        f"""## Finished-run checklist

When this notebook completes, go to:

`/content/drive/MyDrive/{nb['config']['RUN_NAME']}/test_predictions_topk.csv`

Download that file into the project root and name it:

`{nb['download_as']}`

The ensemble commands in `colab/LAUNCH_SHEET.md` expect that exact filename.
""",
        cell_type="markdown",
    )


NOTEBOOKS = [
    {
        "filename": "1_t1_segaware_seed42.ipynb",
        "title": "Notebook 1 - T1 segment-aware ModernBERT-large seed 42",
        "run_label": "T1 segment-aware seed 42",
        "script": T1_SCRIPT,
        "track": "Task 1",
        "role": "Primary segment-aware T1 run.",
        "config": {
            "RUN_NAME": "v3_t1_segaware_seed42",
            "TRAIN_CSV": "segment_aware",
            "TEXT_FIELD": "text_joint",
            "USE_SAMPLE_WEIGHT": True,
            "SEED": 42,
            "EPOCHS": 10,
            "USE_DISTILLATION": False,
            "DISTILL_JSONL_PATH": "/content/reasoning_chains.jsonl",
            "DISTILL_WEIGHT": 0.3,
            "SAVE_TOPK_AND_EMBEDS": True,
        },
        "upload_files": ["task1_segment_aware_train.csv", "task1_segment_aware_test.csv"],
        "expected_files": ["task1_segment_aware_train.csv", "task1_segment_aware_test.csv"],
        "upload_paths": [
            r"C:\Users\akash\Desktop\capstone MGT 599\llm_finetuning\data\segment_aware_task1\task1_segment_aware_train.csv",
            r"C:\Users\akash\Desktop\capstone MGT 599\llm_finetuning\data\segment_aware_task1\task1_segment_aware_test.csv",
        ],
        "expected_outputs": [
            "test_predictions_topk.csv",
            "final_summary.json",
            "train_cls.npy",
            "test_cls.npy",
            "train_meta.csv",
            "test_meta.csv",
        ],
        "download_as": "t1_segaware_seed42_topk.csv",
    },
    {
        "filename": "2_t1_segaware_seed123.ipynb",
        "title": "Notebook 2 - T1 segment-aware ModernBERT-large seed 123",
        "run_label": "T1 segment-aware seed 123",
        "script": T1_SCRIPT,
        "track": "Task 1",
        "role": "Second segment-aware T1 seed for ensemble diversity.",
        "config": {
            "RUN_NAME": "v3_t1_segaware_seed123",
            "TRAIN_CSV": "segment_aware",
            "TEXT_FIELD": "text_joint",
            "USE_SAMPLE_WEIGHT": True,
            "SEED": 123,
            "EPOCHS": 10,
            "USE_DISTILLATION": False,
            "DISTILL_JSONL_PATH": "/content/reasoning_chains.jsonl",
            "DISTILL_WEIGHT": 0.3,
            "SAVE_TOPK_AND_EMBEDS": True,
        },
        "upload_files": ["task1_segment_aware_train.csv", "task1_segment_aware_test.csv"],
        "expected_files": ["task1_segment_aware_train.csv", "task1_segment_aware_test.csv"],
        "upload_paths": [
            r"C:\Users\akash\Desktop\capstone MGT 599\llm_finetuning\data\segment_aware_task1\task1_segment_aware_train.csv",
            r"C:\Users\akash\Desktop\capstone MGT 599\llm_finetuning\data\segment_aware_task1\task1_segment_aware_test.csv",
        ],
        "expected_outputs": [
            "test_predictions_topk.csv",
            "final_summary.json",
            "train_cls.npy",
            "test_cls.npy",
            "train_meta.csv",
            "test_meta.csv",
        ],
        "download_as": "t1_segaware_seed123_topk.csv",
    },
    {
        "filename": "3_t1_raw_seed7.ipynb",
        "title": "Notebook 3 - T1 raw-text ModernBERT-large seed 7",
        "run_label": "T1 raw text seed 7",
        "script": T1_SCRIPT,
        "track": "Task 1",
        "role": "Different input view for T1 ensemble diversity.",
        "config": {
            "RUN_NAME": "v3_t1_raw_seed7",
            "TRAIN_CSV": "raw",
            "TEXT_FIELD": "text",
            "USE_SAMPLE_WEIGHT": False,
            "SEED": 7,
            "EPOCHS": 10,
            "USE_DISTILLATION": False,
            "DISTILL_JSONL_PATH": "/content/reasoning_chains.jsonl",
            "DISTILL_WEIGHT": 0.3,
            "SAVE_TOPK_AND_EMBEDS": True,
        },
        "upload_files": ["task1_train.csv", "task1_test.csv"],
        "expected_files": ["task1_train.csv", "task1_test.csv"],
        "upload_paths": [
            r"C:\Users\akash\Desktop\capstone MGT 599\llm_finetuning\data\task1_train.csv",
            r"C:\Users\akash\Desktop\capstone MGT 599\llm_finetuning\data\task1_test.csv",
        ],
        "expected_outputs": [
            "test_predictions_topk.csv",
            "final_summary.json",
            "train_cls.npy",
            "test_cls.npy",
            "train_meta.csv",
            "test_meta.csv",
        ],
        "download_as": "t1_raw_seed7_topk.csv",
    },
    {
        "filename": "4_t2_segaware_seed42.ipynb",
        "title": "Notebook 4 - T2 segment-aware ModernBERT-large seed 42",
        "run_label": "T2 segment-aware seed 42",
        "script": T2_SCRIPT,
        "track": "Task 2",
        "role": "Primary segment-aware T2 run.",
        "config": {
            "RUN_NAME": "v3_t2_segaware_seed42",
            "USE_SEGMENT_AWARE": True,
            "USE_SAMPLE_WEIGHT": True,
            "SEED": 42,
            "EPOCHS": 12,
            "SAVE_TOPK_AND_EMBEDS": True,
        },
        "upload_files": ["task2_train.csv", "task2_test.csv"],
        "expected_files": ["task2_train.csv", "task2_test.csv"],
        "upload_paths": [
            r"C:\Users\akash\Desktop\capstone MGT 599\llm_finetuning\data\segment_aware_task2\task2_train.csv",
            r"C:\Users\akash\Desktop\capstone MGT 599\llm_finetuning\data\segment_aware_task2\task2_test.csv",
        ],
        "expected_outputs": ["test_predictions_topk.csv", "final_summary.json", "test_cls.npy"],
        "download_as": "t2_segaware_seed42_topk.csv",
    },
    {
        "filename": "5_t2_segaware_seed123.ipynb",
        "title": "Notebook 5 - T2 segment-aware ModernBERT-large seed 123",
        "run_label": "T2 segment-aware seed 123",
        "script": T2_SCRIPT,
        "track": "Task 2",
        "role": "Second segment-aware T2 seed for ensemble diversity.",
        "config": {
            "RUN_NAME": "v3_t2_segaware_seed123",
            "USE_SEGMENT_AWARE": True,
            "USE_SAMPLE_WEIGHT": True,
            "SEED": 123,
            "EPOCHS": 12,
            "SAVE_TOPK_AND_EMBEDS": True,
        },
        "upload_files": ["task2_train.csv", "task2_test.csv"],
        "expected_files": ["task2_train.csv", "task2_test.csv"],
        "upload_paths": [
            r"C:\Users\akash\Desktop\capstone MGT 599\llm_finetuning\data\segment_aware_task2\task2_train.csv",
            r"C:\Users\akash\Desktop\capstone MGT 599\llm_finetuning\data\segment_aware_task2\task2_test.csv",
        ],
        "expected_outputs": ["test_predictions_topk.csv", "final_summary.json", "test_cls.npy"],
        "download_as": "t2_segaware_seed123_topk.csv",
    },
    {
        "filename": "6_t2_segaware_seed7.ipynb",
        "title": "Notebook 6 - T2 segment-aware ModernBERT-large seed 7",
        "run_label": "T2 segment-aware seed 7",
        "script": T2_SCRIPT,
        "track": "Task 2",
        "role": "Third segment-aware T2 seed for ensemble diversity.",
        "config": {
            "RUN_NAME": "v3_t2_segaware_seed7",
            "USE_SEGMENT_AWARE": True,
            "USE_SAMPLE_WEIGHT": True,
            "SEED": 7,
            "EPOCHS": 12,
            "SAVE_TOPK_AND_EMBEDS": True,
        },
        "upload_files": ["task2_train.csv", "task2_test.csv"],
        "expected_files": ["task2_train.csv", "task2_test.csv"],
        "upload_paths": [
            r"C:\Users\akash\Desktop\capstone MGT 599\llm_finetuning\data\segment_aware_task2\task2_train.csv",
            r"C:\Users\akash\Desktop\capstone MGT 599\llm_finetuning\data\segment_aware_task2\task2_test.csv",
        ],
        "expected_outputs": ["test_predictions_topk.csv", "final_summary.json", "test_cls.npy"],
        "download_as": "t2_segaware_seed7_topk.csv",
    },
]


NOTEBOOKS.extend([
    {
        "filename": "7_t1_raw_seed42.ipynb",
        "title": "Notebook 7 - T1 raw-text ModernBERT-large seed 42",
        "run_label": "T1 raw text seed 42",
        "script": T1_SCRIPT,
        "track": "Task 1",
        "role": "Wave 2 raw-text seed for the 75-plus ensemble push.",
        "config": {
            "RUN_NAME": "v3_t1_raw_seed42",
            "TRAIN_CSV": "raw",
            "TEXT_FIELD": "text",
            "USE_SAMPLE_WEIGHT": False,
            "SEED": 42,
            "EPOCHS": 10,
            "USE_DISTILLATION": False,
            "DISTILL_JSONL_PATH": "/content/reasoning_chains.jsonl",
            "DISTILL_WEIGHT": 0.3,
            "SAVE_TOPK_AND_EMBEDS": False,
        },
        "upload_files": ["task1_train.csv", "task1_test.csv"],
        "expected_files": ["task1_train.csv", "task1_test.csv"],
        "upload_paths": [
            r"C:\Users\akash\Desktop\capstone MGT 599\llm_finetuning\data\task1_train.csv",
            r"C:\Users\akash\Desktop\capstone MGT 599\llm_finetuning\data\task1_test.csv",
        ],
        "expected_outputs": ["test_predictions_topk.csv", "final_summary.json", "industry_classes.npy"],
        "download_as": "t1_raw_seed42_topk.csv",
    },
    {
        "filename": "8_t1_raw_seed123.ipynb",
        "title": "Notebook 8 - T1 raw-text ModernBERT-large seed 123",
        "run_label": "T1 raw text seed 123",
        "script": T1_SCRIPT,
        "track": "Task 1",
        "role": "Wave 2 raw-text seed for the 75-plus ensemble push.",
        "config": {
            "RUN_NAME": "v3_t1_raw_seed123",
            "TRAIN_CSV": "raw",
            "TEXT_FIELD": "text",
            "USE_SAMPLE_WEIGHT": False,
            "SEED": 123,
            "EPOCHS": 10,
            "USE_DISTILLATION": False,
            "DISTILL_JSONL_PATH": "/content/reasoning_chains.jsonl",
            "DISTILL_WEIGHT": 0.3,
            "SAVE_TOPK_AND_EMBEDS": False,
        },
        "upload_files": ["task1_train.csv", "task1_test.csv"],
        "expected_files": ["task1_train.csv", "task1_test.csv"],
        "upload_paths": [
            r"C:\Users\akash\Desktop\capstone MGT 599\llm_finetuning\data\task1_train.csv",
            r"C:\Users\akash\Desktop\capstone MGT 599\llm_finetuning\data\task1_test.csv",
        ],
        "expected_outputs": ["test_predictions_topk.csv", "final_summary.json", "industry_classes.npy"],
        "download_as": "t1_raw_seed123_topk.csv",
    },
    {
        "filename": "9_t1_segaware_seed7.ipynb",
        "title": "Notebook 9 - T1 segment-aware ModernBERT-large seed 7",
        "run_label": "T1 segment-aware seed 7",
        "script": T1_SCRIPT,
        "track": "Task 1",
        "role": "Wave 2 segment-aware third seed for ensemble diversity.",
        "config": {
            "RUN_NAME": "v3_t1_segaware_seed7",
            "TRAIN_CSV": "segment_aware",
            "TEXT_FIELD": "text_joint",
            "USE_SAMPLE_WEIGHT": True,
            "SEED": 7,
            "EPOCHS": 10,
            "USE_DISTILLATION": False,
            "DISTILL_JSONL_PATH": "/content/reasoning_chains.jsonl",
            "DISTILL_WEIGHT": 0.3,
            "SAVE_TOPK_AND_EMBEDS": False,
        },
        "upload_files": ["task1_segment_aware_train.csv", "task1_segment_aware_test.csv"],
        "expected_files": ["task1_segment_aware_train.csv", "task1_segment_aware_test.csv"],
        "upload_paths": [
            r"C:\Users\akash\Desktop\capstone MGT 599\llm_finetuning\data\segment_aware_task1\task1_segment_aware_train.csv",
            r"C:\Users\akash\Desktop\capstone MGT 599\llm_finetuning\data\segment_aware_task1\task1_segment_aware_test.csv",
        ],
        "expected_outputs": ["test_predictions_topk.csv", "final_summary.json", "industry_classes.npy"],
        "download_as": "t1_segaware_seed7_topk.csv",
    },
    {
        "filename": "10_t1_segprimary_seed7.ipynb",
        "title": "Notebook 10 - T1 segment-primary ModernBERT-large seed 7",
        "run_label": "T1 segment-primary seed 7",
        "script": T1_SCRIPT,
        "track": "Task 1",
        "role": "Wave 2 segment-only-leaning input variant for diversity.",
        "config": {
            "RUN_NAME": "v3_t1_segprimary_seed7",
            "TRAIN_CSV": "segment_aware",
            "TEXT_FIELD": "text_primary",
            "USE_SAMPLE_WEIGHT": True,
            "SEED": 7,
            "EPOCHS": 10,
            "USE_DISTILLATION": False,
            "DISTILL_JSONL_PATH": "/content/reasoning_chains.jsonl",
            "DISTILL_WEIGHT": 0.3,
            "SAVE_TOPK_AND_EMBEDS": False,
        },
        "upload_files": ["task1_segment_aware_train.csv", "task1_segment_aware_test.csv"],
        "expected_files": ["task1_segment_aware_train.csv", "task1_segment_aware_test.csv"],
        "upload_paths": [
            r"C:\Users\akash\Desktop\capstone MGT 599\llm_finetuning\data\segment_aware_task1\task1_segment_aware_train.csv",
            r"C:\Users\akash\Desktop\capstone MGT 599\llm_finetuning\data\segment_aware_task1\task1_segment_aware_test.csv",
        ],
        "expected_outputs": ["test_predictions_topk.csv", "final_summary.json", "industry_classes.npy"],
        "download_as": "t1_segprimary_seed7_topk.csv",
    },
])


for nb in NOTEBOOKS:
    cells = [
        header_cell(nb),
        make_cell('!pip -q install -U "transformers>=4.48.0" datasets accelerate scikit-learn pandas numpy tqdm pytorch-optimizer'),
        upload_cell(nb),
        verify_cell(nb),
    ]

    if nb["track"] == "Task 2":
        cells.append(
            make_cell(
                """import os, shutil
if os.path.exists("/content/task2_train.csv"):
    shutil.move("/content/task2_train.csv", "/content/segment_aware_t2_train.csv")
if os.path.exists("/content/task2_test.csv"):
    shutil.move("/content/task2_test.csv", "/content/segment_aware_t2_test.csv")
print("Task 2 training path:", "OK" if os.path.exists("/content/segment_aware_t2_train.csv") else "MISSING")
print("Task 2 test path:", "OK" if os.path.exists("/content/segment_aware_t2_test.csv") else "MISSING")
"""
            )
        )

    cells.append(make_cell(replace_config(nb["script"], nb["config"])))
    cells.append(finish_cell(nb))

    out_path = NB_OUT / nb["filename"]
    out_path.write_text(json.dumps(make_notebook(cells), indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")

print(f"\nDone. {len(NOTEBOOKS)} notebooks in {NB_OUT}")
