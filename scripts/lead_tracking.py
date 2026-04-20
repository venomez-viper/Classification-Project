# lead_tracking.py
# Lead coordination and progress tracking
# Sets up the team tracker and creates all doc templates.
# Run this first before anyone else runs their scripts.
# Usage: python lead_tracking.py

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
    print("setting up team tracker and doc templates...\n")

    # build the team tracker csv
    tracker = pd.DataFrame([
        ["Member 1",  "Lead, coordination, weekly reports",   "In Progress", "phase_summary.md"],
        ["Member 2",  "Dashboard and descriptive analytics",  "Pending",     "dashboard charts + dashboard_findings_summary.md"],
        ["Member 3",  "Task 1 feature engineering",           "Pending",     "task1_features_full_v1.csv"],
        ["Member 4",  "Task 2 feature engineering",           "Pending",     "task2_features_full_v1.csv"],
        ["Member 5",  "Feature review and model-ready files", "Pending",     "task1_model_ready_v1.csv / task2_model_ready_v1.csv"],
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

    print("\nall templates created\n")

    # file audit - check what outputs exist so far
    print("file audit:")
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

    print("\ndone.")


if __name__ == "__main__":
    main()
