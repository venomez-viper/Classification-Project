# akash_lead_tracking.py
# Lead coordination and progress tracking
# This script sets up the team tracker and creates all doc templates.
# Run this first before anyone else runs their scripts.
# Usage: python akash_lead_tracking.py

from pathlib import Path
import pandas as pd

from common_utils import (
    BASE_PATH,
    WEEKLY_REPORT_PATH,
    HANDOFF_PATH,
    FINDINGS_PATH,
    ensure_folders,
)


def main():
    ensure_folders()
    print("Creating team tracker and documentation templates...\n")

    # build the team tracker csv
    tracker = pd.DataFrame([
        ["Akash",              "Lead, coordination, weekly reports",   "In Progress", "phase_summary.md"],
        ["Tserennad Batkhuu",  "Dashboard and descriptive analytics",  "Pending",     "01_descriptive_dashboard charts + dashboard_findings_summary.md"],
        ["Srilaxmi Ganjipalli","Task 1 feature engineering",           "Pending",     "task1_features_full_v1.csv"],
        ["Vishal Ganjipalli",  "Task 2 feature engineering",           "Pending",     "task2_features_full_v1.csv"],
        ["Subasree Segar",     "Feature review and model-ready files", "Pending",     "task1_model_ready_v1.csv / task2_model_ready_v1.csv"],
    ], columns=["Team Member", "Assigned Role", "Status", "Expected Output"])

    tracker_file = WEEKLY_REPORT_PATH / "team_progress_tracker.csv"
    tracker.to_csv(tracker_file, index=False)
    print(f"  Tracker saved  -> {tracker_file}")

    # handoff note template
    handoff_text = """# Team Handoff Note

## Completed by
[Write your name]

## Section completed
[Write your section name]

## Files created
-

## Main findings
-

## Issues faced
-

## What the next person should do
-
"""
    handoff_file = HANDOFF_PATH / "handoff_template.md"
    handoff_file.write_text(handoff_text, encoding="utf-8")
    print(f"  Handoff template saved -> {handoff_file}")

    # weekly report template
    weekly_text = """# Weekly Progress Report

## Team Member
[Write your name]

## Work completed this week
-
-
-

## Outputs submitted
-
-

## Key findings
-
-

## Challenges faced
-
-

## Next steps
-
-
"""
    weekly_file = WEEKLY_REPORT_PATH / "weekly_report_template.md"
    weekly_file.write_text(weekly_text, encoding="utf-8")
    print(f"  Weekly report template saved -> {weekly_file}")

    # phase summary template
    phase_text = """# Phase Summary

## Phase objective
Describe the purpose of this project phase.

## Completed work
-
-
-

## Current outputs
-
-
-

## Risks or blockers
-
-

## Next phase recommendation
-
-
"""
    summary_file = FINDINGS_PATH / "phase_summary_template.md"
    summary_file.write_text(phase_text, encoding="utf-8")
    print(f"  Phase summary template saved -> {summary_file}")

    print("\nAll documentation templates created.\n")

    # file audit - check what outputs exist so far
    print("=== File Audit ===")
    audit = {
        "outputs/dashboard/"    : "*.png",
        "outputs/features/task1/": "*.csv",
        "outputs/features/task2/": "*.csv",
        "outputs/model_ready/"  : "*.csv",
        "docs/findings_summary/": "*.md",
    }
    for folder, pat in audit.items():
        full_path = BASE_PATH / folder
        files = list(full_path.glob(pat)) if full_path.exists() else []
        status = f"{len(files)} file(s)" if files else "EMPTY"
        print(f"  {folder}: {status}")
        for f in files:
            print(f"    - {f.name}")

    print("\nDone. Share this guide and the tracker with the team.")


if __name__ == "__main__":
    main()
