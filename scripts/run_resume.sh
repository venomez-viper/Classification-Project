#!/usr/bin/env bash
# run_resume.sh — resumes from V6 onward. BGE embeddings are cached so V6
# training is fast. Forces UTF-8 stdout to bypass Windows cp1252 issues.

set +e
cd "$(dirname "$0")/.."
PROJ="$(pwd)"

export PYTHONIOENCODING=utf-8
export PYTHONUTF8=1

LOG="$PROJ/overnight_run.log"
echo "" >> "$LOG"
echo "=== Resume chain started at $(date) ===" >> "$LOG"

run_step() {
    local label="$1"
    local script="$2"
    {
        echo ""
        echo "================================================================"
        echo "[$label] starting at $(date)"
        echo "================================================================"
    } >> "$LOG"
    python -u "$script" >> "$LOG" 2>&1
    local rc=$?
    if [ $rc -eq 0 ]; then
        echo "[$label] completed at $(date)" >> "$LOG"
    else
        echo "[$label] FAILED rc=$rc at $(date) (continuing)" >> "$LOG"
    fi
}

run_step "V6 BGE retrain (cached embeddings)" "scripts/train_cascade_v6_bge.py"
run_step "V7 SetFit fine-tune"                "scripts/train_cascade_v7_setfit.py"
run_step "V8 mega-ensemble"                   "scripts/train_cascade_v8_ensemble.py"
run_step "FINALIZE"                           "scripts/finalize_results.py"

echo "" >> "$LOG"
echo "=== Resume chain finished at $(date) ===" >> "$LOG"
