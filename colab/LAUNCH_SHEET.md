# Colab Launch Sheet - 6 Parallel Runs

Goal: open all six notebooks in separate Colab tabs, run them at the same time, then ensemble the top-k outputs locally.

Start with the three Task 1 tabs first if Colab limits GPU sessions. Task 1 is the score we are trying to lift fastest.

Important Task 2 fix: regenerated notebooks now use 10-digit subindustry codes. If an older T2 run prints codes like `03103001001`, that run used the broken 11-digit padding and should be rerun from the regenerated notebooks.

## 0. Regenerate notebooks if needed

From the project root:

```powershell
python colab\generate_notebooks.py
```

This writes the six original notebooks plus four Task 1 Wave 2 notebooks into `colab/notebooks/`.

## 1. Open these six notebooks in six Colab tabs

| Tab | Notebook | Track | Upload files | Download finished file as |
|---|---|---|---|---|
| 1 | `colab/notebooks/1_t1_segaware_seed42.ipynb` | Task 1 | `task1_segment_aware_train.csv`, `task1_segment_aware_test.csv` | `t1_segaware_seed42_topk.csv` |
| 2 | `colab/notebooks/2_t1_segaware_seed123.ipynb` | Task 1 | `task1_segment_aware_train.csv`, `task1_segment_aware_test.csv` | `t1_segaware_seed123_topk.csv` |
| 3 | `colab/notebooks/3_t1_raw_seed7.ipynb` | Task 1 | `task1_train.csv`, `task1_test.csv` | `t1_raw_seed7_topk.csv` |
| 4 | `colab/notebooks/4_t2_segaware_seed42.ipynb` | Task 2 | `task2_train.csv`, `task2_test.csv` from `segment_aware_task2` | `t2_segaware_seed42_topk.csv` |
| 5 | `colab/notebooks/5_t2_segaware_seed123.ipynb` | Task 2 | `task2_train.csv`, `task2_test.csv` from `segment_aware_task2` | `t2_segaware_seed123_topk.csv` |
| 6 | `colab/notebooks/6_t2_segaware_seed7.ipynb` | Task 2 | `task2_train.csv`, `task2_test.csv` from `segment_aware_task2` | `t2_segaware_seed7_topk.csv` |

## 1B. Wave 2 Task 1 notebooks for the 75-plus push

Run these after the first three Task 1 notebooks finish, or immediately if Colab Pro+ gives you more GPUs. They are top-k only, no embeddings, so they finish the post-training save step faster.

| Tab | Notebook | Track | Upload files | Download finished file as |
|---|---|---|---|---|
| 7 | `colab/notebooks/7_t1_raw_seed42.ipynb` | Task 1 | `task1_train.csv`, `task1_test.csv` | `t1_raw_seed42_topk.csv` |
| 8 | `colab/notebooks/8_t1_raw_seed123.ipynb` | Task 1 | `task1_train.csv`, `task1_test.csv` | `t1_raw_seed123_topk.csv` |
| 9 | `colab/notebooks/9_t1_segaware_seed7.ipynb` | Task 1 | `task1_segment_aware_train.csv`, `task1_segment_aware_test.csv` | `t1_segaware_seed7_topk.csv` |
| 10 | `colab/notebooks/10_t1_segprimary_seed7.ipynb` | Task 1 | `task1_segment_aware_train.csv`, `task1_segment_aware_test.csv` | `t1_segprimary_seed7_topk.csv` |

## 2. Windows upload paths

Use these files when each notebook asks for uploads:

| Needed in notebook | Windows path |
|---|---|
| `task1_train.csv` | `llm_finetuning\data\task1_train.csv` |
| `task1_test.csv` | `llm_finetuning\data\task1_test.csv` |
| `task1_segment_aware_train.csv` | `llm_finetuning\data\segment_aware_task1\task1_segment_aware_train.csv` |
| `task1_segment_aware_test.csv` | `llm_finetuning\data\segment_aware_task1\task1_segment_aware_test.csv` |
| Task 2 `task2_train.csv` | `llm_finetuning\data\segment_aware_task2\task2_train.csv` |
| Task 2 `task2_test.csv` | `llm_finetuning\data\segment_aware_task2\task2_test.csv` |

The Task 2 notebooks rename the uploaded files inside Colab to `segment_aware_t2_train.csv` and `segment_aware_t2_test.csv`, which is what the trainer expects.

## 3. Parallel launch routine

1. Open Tab 1, choose GPU runtime, click `Runtime -> Run all`.
2. When upload appears, upload only that tab's required files.
3. Immediately move to Tab 2 and repeat.
4. Start Tabs 1-3 first for Task 1.
5. Start Tabs 4-6 after the Task 1 tabs are running.
6. Leave every tab open until it prints the final summary and writes to Drive.

Expected Drive output folder pattern:

```text
/content/drive/MyDrive/<RUN_NAME>/test_predictions_topk.csv
```

## 4. Download outputs into the project root

Download only `test_predictions_topk.csv` from each Drive folder and rename it exactly:

| Drive folder | Local filename |
|---|---|
| `v3_t1_segaware_seed42` | `t1_segaware_seed42_topk.csv` |
| `v3_t1_segaware_seed123` | `t1_segaware_seed123_topk.csv` |
| `v3_t1_raw_seed7` | `t1_raw_seed7_topk.csv` |
| `v3_t2_segaware_seed42` | `t2_segaware_seed42_topk.csv` |
| `v3_t2_segaware_seed123` | `t2_segaware_seed123_topk.csv` |
| `v3_t2_segaware_seed7` | `t2_segaware_seed7_topk.csv` |

## 5. Ensemble locally after downloads finish

Task 1 ensemble:

```powershell
python scripts\ensemble_models.py --task 1 `
  --inputs modernbert_large_v3_test_predictions_topk.csv t1_segaware_seed42_topk.csv t1_segaware_seed123_topk.csv t1_raw_seed7_topk.csv `
  --weights 0.8 1.1 1.0 1.1 `
  --out t1_ensemble_4models.csv

python scripts\analyze_predictions.py t1_ensemble_4models.csv --name "T1 ensemble x4"
```

Task 1 Wave 2 ensemble after notebooks 7-10 finish:

```powershell
python scripts\ensemble_models.py --task 1 `
  --inputs modernbert_large_v3_test_predictions_topk.csv t1_segaware_seed42_topk.csv t1_segaware_seed123_topk.csv t1_raw_seed7_topk.csv t1_raw_seed42_topk.csv t1_raw_seed123_topk.csv t1_segaware_seed7_topk.csv t1_segprimary_seed7_topk.csv `
  --weights 0.7 1.0 1.0 1.1 1.0 1.0 1.0 0.9 `
  --out t1_ensemble_8models.csv

python scripts\analyze_predictions.py t1_ensemble_8models.csv --name "T1 ensemble x8"
```

Task 2 ensemble:

```powershell
python scripts\ensemble_models.py --task 2 `
  --inputs t2_segaware_seed42_topk.csv t2_segaware_seed123_topk.csv t2_segaware_seed7_topk.csv `
  --weights 1.0 1.0 1.0 `
  --out t2_ensemble_3models.csv
```

## 6. What to watch

- If a notebook fails before training starts, rerun from the upload cell after confirming the files are present.
- If a notebook runs out of memory, lower batch size in the trainer cell and rerun that tab only.
- If Colab limits GPUs, keep Tabs 1-3 running first and queue Tabs 4-6 afterward.
- Do not mix Task 2 outputs into the Task 1 ensemble command.

## Realistic same-day expectation

| Metric | Current | 6-run ensemble target range |
|---|---:|---:|
| Task 1 macro F1 | 70.92% | 73-76% |
| Task 2 macro F1 | 55.41% cascade baseline | 60-68% |

The six-tab run is the fastest legitimate lift path. A true 80% Task 1 result likely needs a second wave after these numbers come back.

For the 75-plus Task 1 push, run the Wave 2 notebooks and use `t1_ensemble_8models.csv` as the candidate headline. Do not tune ensemble weights on the official test labels; use the predeclared weights above unless we add a separate validation-output export.
