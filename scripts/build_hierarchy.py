from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.cascade_common import (
    DEFAULT_HIERARCHY_JSON,
    DEFAULT_TASK1_CSV,
    build_taxonomy_tree,
    load_task1_training_frame,
    save_json,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a GECS hierarchy JSON from Task 1 labels.")
    parser.add_argument("--input", default=str(DEFAULT_TASK1_CSV), help="Task 1 cleaned CSV path")
    parser.add_argument("--output", default=str(DEFAULT_HIERARCHY_JSON), help="Output JSON path")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    frame = load_task1_training_frame(args.input)
    tree = build_taxonomy_tree(frame)
    output_path = save_json(tree, args.output)

    summary = tree["summary"]
    print(f"Hierarchy saved to {output_path}")
    print(
        "Rows={rows} | sectors={sector_count} | groups={group_count} | codes={code_count}".format(
            **summary
        )
    )


if __name__ == "__main__":
    main()
