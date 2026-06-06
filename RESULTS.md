# Task 1 — Final Results

All evaluated on the case-standard row-level 80/20 split
(`task1_train.csv` -&gt; `task1_test.csv`).

## Leaderboard

| Rank | Approach | Macro F1 | Top-10 pass | Target &gt;=75% |
|---|---|---|---|---|
| 1 | V8 (mega-ensemble of all encoders + TF-IDF) | 68.42% | — | FAIL |
| 2 | V6 (hybrid TF-IDF + BGE-base) | 67.70% | 2/10 | FAIL |
| 3 | V5 (hybrid TF-IDF + MiniLM) | 67.11% | 2/10 | FAIL |
| 4 | V2 (cascade, V3 features, CompanyId split) | 56.80% | 1/10 | FAIL |
| — | V4 (MiniLM embeddings, row-level) | not run | — | — |
| — | V7 (SetFit fine-tune + classifier) | not run | — | — |

## Winner

**V8 (mega-ensemble of all encoders + TF-IDF)** — Macro F1 68.42% — top-10 None/10

[FAIL] Below case requirement of &gt;=75% Macro F1 (gap: 6.58pp).

### Winner config
```json
{
  "version": "v8-ensemble",
  "available_encoders": [
    "minilm",
    "bge"
  ],
  "results": {
    "minilm": {
      "f1": 0.6710676790656732,
      "C": 1.0,
      "top10_pass": 2
    },
    "bge": {
      "f1": 0.6763385207451689,
      "C": 2.0,
      "top10_pass": 2
    },
    "MEGA_ENSEMBLE": {
      "f1": 0.6841770935528076,
      "C": 1.0,
      "top10_pass": 2
    }
  },
  "winner": "MEGA_ENSEMBLE",
  "best_f1": 68.42,
  "target_met": false
}
```


## Audit history

See [`CASCADE_AUDIT.md`](CASCADE_AUDIT.md) for full chronological
record of problems found, fixes applied, and methodology.
