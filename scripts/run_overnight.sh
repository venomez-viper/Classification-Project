#!/usr/bin/env bash
# run_overnight.sh — runs V5 → V6 → V7 → V8 → finalize sequentially.
# Each step uses python -u for unbuffered output. Failures don't kill the chain.

set +e
cd "$(dirname "$0")/.."
PROJ="$(pwd)"

# Force UTF-8 stdout so ←, →, ≥, ✓ etc. don't crash on Windows cp1252
export PYTHONIOENCODING=utf-8
export PYTHONUTF8=1

LOG="$PROJ/overnight_run.log"
echo "=== Overnight chain started at $(date) ===" | tee "$LOG"

run_step() {
    local label="$1"
    local script="$2"
    echo "" | tee -a "$LOG"
    echo "================================================================" | tee -a "$LOG"
    echo "[$label] starting at $(date)" | tee -a "$LOG"
    echo "================================================================" | tee -a "$LOG"
    if python -u "$script" 2>&1 | tee -a "$LOG"; then
        echo "[$label] completed at $(date)" | tee -a "$LOG"
    else
        echo "[$label] FAILED at $(date) (continuing chain)" | tee -a "$LOG"
    fi
}

run_step "V5 hybrid (cached MiniLM + TF-IDF)"   "scripts/train_cascade_v5_hybrid.py"
run_step "V6 BGE encoder + hybrid"               "scripts/train_cascade_v6_bge.py"
run_step "V7 SetFit fine-tune"                   "scripts/train_cascade_v7_setfit.py"
run_step "V8 mega-ensemble"                      "scripts/train_cascade_v8_ensemble.py"
run_step "FINALIZE"                              "scripts/finalize_results.py"

echo "" | tee -a "$LOG"
echo "=== Overnight chain finished at $(date) ===" | tee -a "$LOG"
