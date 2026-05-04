from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


DEFAULT_TASK1_CSV = Path("data/cleaned/task1_clean.csv")
DEFAULT_HIERARCHY_JSON = Path("models/cascade_taxonomy_tree.json")
DEFAULT_MODELS_DIR = Path("models")

TEXT_COLUMNS = ("LongProfile", "SegmentName", "SegmentDescription")
TARGET_COLUMN = "MstarGlobal"


def normalize_code(value: Any) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if not text:
        return ""
    if text.endswith(".0"):
        text = text[:-2]
    digits = "".join(ch for ch in text if ch.isdigit())
    return digits.zfill(8) if digits else ""


def build_combined_text(frame: pd.DataFrame) -> pd.Series:
    parts = []
    for column in TEXT_COLUMNS:
        if column in frame.columns:
            parts.append(frame[column].fillna("").astype(str).str.strip())
        else:
            parts.append(pd.Series([""] * len(frame), index=frame.index, dtype="object"))
    combined = (parts[0] + " " + parts[1] + " " + parts[2]).str.replace(r"\s+", " ", regex=True)
    return combined.str.strip()


def load_task1_training_frame(csv_path: Path | str = DEFAULT_TASK1_CSV) -> pd.DataFrame:
    csv_path = Path(csv_path)
    frame = pd.read_csv(csv_path)
    if TARGET_COLUMN not in frame.columns:
        raise ValueError(f"Expected '{TARGET_COLUMN}' in {csv_path}")

    working = frame.loc[:, [c for c in TEXT_COLUMNS if c in frame.columns] + [TARGET_COLUMN]].copy()
    working["code"] = working[TARGET_COLUMN].map(normalize_code)
    working = working[working["code"] != ""].copy()
    working["sector_code"] = working["code"].str[:3]
    working["group_code"] = working["code"].str[:5]
    working["combined_text"] = build_combined_text(working)
    return working


def build_taxonomy_tree(frame: pd.DataFrame) -> dict[str, Any]:
    sector_to_groups = (
        frame.groupby("sector_code")["group_code"]
        .apply(lambda values: sorted(set(values)))
        .sort_index()
        .to_dict()
    )
    group_to_codes = (
        frame.groupby("group_code")["code"]
        .apply(lambda values: sorted(set(values)))
        .sort_index()
        .to_dict()
    )
    sector_to_codes = {
        sector: sorted({code for group in groups for code in group_to_codes[group]})
        for sector, groups in sector_to_groups.items()
    }
    code_counts = frame["code"].value_counts().sort_index().to_dict()

    return {
        "summary": {
            "rows": int(len(frame)),
            "sector_count": int(frame["sector_code"].nunique()),
            "group_count": int(frame["group_code"].nunique()),
            "code_count": int(frame["code"].nunique()),
        },
        "sector_to_groups": sector_to_groups,
        "group_to_codes": group_to_codes,
        "sector_to_codes": sector_to_codes,
        "code_counts": code_counts,
    }


def save_json(payload: dict[str, Any], output_path: Path | str) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return output_path
