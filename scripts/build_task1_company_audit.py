from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task1_segment_aware_common import build_task1_segment_aware_splits, save_json, summarize_split

OUT_DIR = ROOT / "models_segment_aware"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Building Task 1 company ambiguity audit...", flush=True)
    train, test, summary = build_task1_segment_aware_splits()

    train_path = OUT_DIR / "task1_train_enriched.csv"
    test_path = OUT_DIR / "task1_test_enriched.csv"
    train.to_csv(train_path, index=False)
    test.to_csv(test_path, index=False)

    company_examples = (
        pd.concat([train, test], ignore_index=True)
        .sort_values(
            ["company_num_codes", "company_dominant_share", "longprofile_code_count", "sample_weight"],
            ascending=[False, True, False, True],
        )
        [[
            "CompanyId",
            "code",
            "company_dominant_code",
            "company_num_codes",
            "company_dominant_share",
            "longprofile_code_count",
            "row_is_ambiguous_supervision",
            "sample_weight",
            "segment_text",
        ]]
        .drop_duplicates(subset=["CompanyId", "code"])
        .head(50)
    )
    company_examples_path = OUT_DIR / "task1_ambiguous_company_examples.csv"
    company_examples.to_csv(company_examples_path, index=False)

    audit_summary = {
        "overview": summary,
        "train": summarize_split(train, "train"),
        "test": summarize_split(test, "test"),
        "artifacts": {
            "train_enriched_csv": str(train_path.relative_to(ROOT)),
            "test_enriched_csv": str(test_path.relative_to(ROOT)),
            "ambiguous_examples_csv": str(company_examples_path.relative_to(ROOT)),
        },
        "weighting_rules": {
            "multi_code_company": "downweight to 0.70x before other adjustments",
            "ambiguous_longprofile": "downweight to 0.80x",
            "off_dominant_row": "downweight if row label disagrees with company or longprofile dominant code",
            "largest_share_segment": "small positive lift",
        },
    }
    save_json(audit_summary, OUT_DIR / "company_ambiguity_summary.json")

    print(json.dumps(audit_summary, indent=2))
    print(f"\nSaved enriched splits to {OUT_DIR}", flush=True)


if __name__ == "__main__":
    main()
