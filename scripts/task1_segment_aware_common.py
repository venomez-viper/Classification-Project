from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_CSV = ROOT / "data/raw/task1_gecs_classification_final (2).csv"
TRAIN_CSV = ROOT / "llm_finetuning/data/task1_train.csv"
TEST_CSV = ROOT / "llm_finetuning/data/task1_test.csv"

TEXT_COLUMNS = ("LongProfile", "SegmentName", "SegmentDescription")
TARGET_COLUMN = "MstarGlobal"

_BP = re.compile(r"\bThe [Cc]ompan(?:y|ies)\b", re.IGNORECASE)


def clean_text(value: Any) -> str:
    text = re.sub(r"\s{2,}", " ", _BP.sub(" ", str(value or ""))).strip()
    return text


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


def normalize_longprofile(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def build_combined_text(frame: pd.DataFrame) -> pd.Series:
    parts: list[pd.Series] = []
    for column in TEXT_COLUMNS:
        if column in frame.columns:
            parts.append(frame[column].fillna("").astype(str).str.strip())
        else:
            parts.append(pd.Series([""] * len(frame), index=frame.index, dtype="object"))
    combined = (parts[0] + " " + parts[1] + " " + parts[2]).str.replace(r"\s+", " ", regex=True)
    return combined.str.strip()


def _entropy_from_counts(values: pd.Series) -> float:
    probs = values.value_counts(normalize=True).to_numpy(dtype=np.float64)
    if len(probs) <= 1:
        return 0.0
    return float(-(probs * np.log2(probs)).sum())


def load_raw_task1_frame(csv_path: Path | str = RAW_CSV) -> pd.DataFrame:
    csv_path = Path(csv_path)
    raw = pd.read_csv(csv_path)
    raw["code"] = raw[TARGET_COLUMN].map(normalize_code)
    raw = raw[raw["code"] != ""].copy()
    raw["combined"] = build_combined_text(raw)
    raw["segment_text"] = (
        raw["SegmentName"].fillna("").astype(str).str.strip()
        + " "
        + raw["SegmentDescription"].fillna("").astype(str).str.strip()
    ).str.replace(r"\s+", " ", regex=True).str.strip()
    raw["company_text"] = raw["LongProfile"].fillna("").map(clean_text)
    raw["longprofile_key"] = raw["LongProfile"].map(normalize_longprofile)
    raw["sector_code"] = raw["code"].str[:3]
    raw["group_code"] = raw["code"].str[:5]
    return raw


def build_company_profiles(raw: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for company_id, group in raw.groupby("CompanyId", dropna=False):
        codes = group["code"].astype(str)
        counts = codes.value_counts()
        dominant_code = str(counts.index[0])
        dominant_share = float(counts.iloc[0] / len(group))
        rows.append(
            {
                "CompanyId": company_id,
                "company_row_count": int(len(group)),
                "company_num_codes": int(codes.nunique()),
                "company_dominant_code": dominant_code,
                "company_dominant_share": dominant_share,
                "company_code_entropy": _entropy_from_counts(codes),
                "company_num_segments": int(group["SegmentName"].nunique()),
                "company_is_multicode": int(codes.nunique() > 1),
                "company_is_ambiguous": int(codes.nunique() > 1 or dominant_share < 0.70),
                "company_max_revenue_share": float(group["revenue_share"].fillna(0.0).abs().max()),
                "company_share_std": float(group["revenue_share"].fillna(0.0).std() or 0.0),
            }
        )
    return pd.DataFrame(rows)


def build_longprofile_profiles(raw: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    keyed = raw[raw["longprofile_key"] != ""].copy()
    for longprofile_key, group in keyed.groupby("longprofile_key", dropna=False):
        codes = group["code"].astype(str)
        counts = codes.value_counts()
        dominant_code = str(counts.index[0])
        dominant_share = float(counts.iloc[0] / len(group))
        rows.append(
            {
                "longprofile_key": longprofile_key,
                "longprofile_row_count": int(len(group)),
                "longprofile_company_count": int(group["CompanyId"].nunique()),
                "longprofile_code_count": int(codes.nunique()),
                "longprofile_dominant_code": dominant_code,
                "longprofile_dominant_share": dominant_share,
                "longprofile_code_entropy": _entropy_from_counts(codes),
                "longprofile_is_ambiguous": int(codes.nunique() > 1 or dominant_share < 0.70),
            }
        )
    return pd.DataFrame(rows)


def compute_sample_weights(frame: pd.DataFrame) -> np.ndarray:
    weights = np.ones(len(frame), dtype=np.float64)

    # Downweight rows whose supervision is structurally ambiguous.
    weights *= np.where(frame["company_is_multicode"].to_numpy(dtype=bool), 0.70, 1.10)
    weights *= np.where(frame["longprofile_is_ambiguous"].to_numpy(dtype=bool), 0.80, 1.00)
    weights *= np.where(frame["row_matches_company_dominant"].to_numpy(dtype=bool), 1.05, 0.80)
    weights *= np.where(frame["row_matches_longprofile_dominant"].to_numpy(dtype=bool), 1.00, 0.85)

    # Give a modest lift to the segment most likely to represent the firm.
    if "is_largest_share_segment" in frame.columns:
        largest = frame["is_largest_share_segment"].fillna(False).astype(bool).to_numpy()
        weights *= np.where(largest, 1.10, 1.00)

    if "revenue_share" in frame.columns:
        revenue_share = frame["revenue_share"].fillna(0.0).clip(lower=0.0, upper=1.0).to_numpy(dtype=np.float64)
        weights *= 0.95 + 0.15 * revenue_share

    return np.clip(weights, 0.20, 1.75)


def build_split_frame(
    split_csv: Path | str,
    raw: pd.DataFrame,
    company_profiles: pd.DataFrame,
    longprofile_profiles: pd.DataFrame,
) -> pd.DataFrame:
    split_csv = Path(split_csv)
    split = pd.read_csv(split_csv).copy()
    split["code"] = split["mstar_code"].map(normalize_code)
    split = split[split["code"] != ""].copy()

    raw_dedup = raw.drop_duplicates("combined", keep="first").copy()
    join_cols = [
        "combined",
        "CompanyId",
        "LongProfile",
        "SegmentName",
        "SegmentDescription",
        "revenue_share",
        "is_largest_share_segment",
        "code",
    ]
    split = split.merge(raw_dedup[join_cols], left_on="text", right_on="combined", how="left", suffixes=("", "_raw"))

    split["LongProfile"] = split["LongProfile"].fillna(split["text"])
    split["SegmentName"] = split["SegmentName"].fillna("")
    split["SegmentDescription"] = split["SegmentDescription"].fillna(split["text"])
    split["revenue_share"] = split["revenue_share"].fillna(0.5)
    split["is_largest_share_segment"] = split["is_largest_share_segment"].fillna(False).astype(float)
    unknown_ids = pd.Series("UNKNOWN_" + split.index.astype(str), index=split.index)
    split["CompanyId"] = split["CompanyId"].fillna(unknown_ids)

    split["segment_text"] = (
        split["SegmentName"].fillna("").astype(str).str.strip()
        + " "
        + split["SegmentDescription"].fillna("").astype(str).str.strip()
    ).str.replace(r"\s+", " ", regex=True).str.strip().map(clean_text)
    split["company_text"] = split["LongProfile"].fillna("").map(clean_text)
    split["longprofile_key"] = split["LongProfile"].map(normalize_longprofile)
    split["sector_code"] = split["code"].str[:3]
    split["group_code"] = split["code"].str[:5]

    split = split.merge(company_profiles, on="CompanyId", how="left")
    split = split.merge(longprofile_profiles, on="longprofile_key", how="left")

    split["company_row_count"] = split["company_row_count"].fillna(1).astype(int)
    split["company_num_codes"] = split["company_num_codes"].fillna(1).astype(int)
    split["company_dominant_code"] = split["company_dominant_code"].fillna(split["code"])
    split["company_dominant_share"] = split["company_dominant_share"].fillna(1.0)
    split["company_code_entropy"] = split["company_code_entropy"].fillna(0.0)
    split["company_num_segments"] = split["company_num_segments"].fillna(1).astype(int)
    split["company_is_multicode"] = split["company_is_multicode"].fillna(0).astype(int)
    split["company_is_ambiguous"] = split["company_is_ambiguous"].fillna(0).astype(int)

    split["longprofile_row_count"] = split["longprofile_row_count"].fillna(1).astype(int)
    split["longprofile_company_count"] = split["longprofile_company_count"].fillna(1).astype(int)
    split["longprofile_code_count"] = split["longprofile_code_count"].fillna(1).astype(int)
    split["longprofile_dominant_code"] = split["longprofile_dominant_code"].fillna(split["code"])
    split["longprofile_dominant_share"] = split["longprofile_dominant_share"].fillna(1.0)
    split["longprofile_code_entropy"] = split["longprofile_code_entropy"].fillna(0.0)
    split["longprofile_is_ambiguous"] = split["longprofile_is_ambiguous"].fillna(0).astype(int)

    split["row_matches_company_dominant"] = (split["code"] == split["company_dominant_code"]).astype(int)
    split["row_matches_longprofile_dominant"] = (split["code"] == split["longprofile_dominant_code"]).astype(int)
    split["row_is_ambiguous_supervision"] = (
        (split["company_is_multicode"] == 1) | (split["longprofile_is_ambiguous"] == 1)
    ).astype(int)
    split["sample_weight"] = compute_sample_weights(split)
    return split


def build_task1_segment_aware_splits(
    raw_csv: Path | str = RAW_CSV,
    train_csv: Path | str = TRAIN_CSV,
    test_csv: Path | str = TEST_CSV,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    raw = load_raw_task1_frame(raw_csv)
    company_profiles = build_company_profiles(raw)
    longprofile_profiles = build_longprofile_profiles(raw)
    train = build_split_frame(train_csv, raw, company_profiles, longprofile_profiles)
    test = build_split_frame(test_csv, raw, company_profiles, longprofile_profiles)

    summary = {
        "raw_rows": int(len(raw)),
        "raw_companies": int(raw["CompanyId"].nunique()),
        "raw_codes": int(raw["code"].nunique()),
        "multi_code_companies": int((company_profiles["company_is_multicode"] == 1).sum()),
        "ambiguous_longprofiles": int((longprofile_profiles["longprofile_is_ambiguous"] == 1).sum()),
        "train_rows": int(len(train)),
        "test_rows": int(len(test)),
        "train_ambiguous_rows": int(train["row_is_ambiguous_supervision"].sum()),
        "test_ambiguous_rows": int(test["row_is_ambiguous_supervision"].sum()),
        "train_weight_mean": round(float(train["sample_weight"].mean()), 4),
        "test_weight_mean": round(float(test["sample_weight"].mean()), 4),
    }
    return train, test, summary


def save_json(payload: dict[str, Any], output_path: Path | str) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return output_path


def summarize_split(frame: pd.DataFrame, name: str) -> dict[str, Any]:
    return {
        "name": name,
        "rows": int(len(frame)),
        "companies": int(frame["CompanyId"].nunique()),
        "codes": int(frame["code"].nunique()),
        "ambiguous_rows": int(frame["row_is_ambiguous_supervision"].sum()),
        "multi_code_company_rows": int(frame["company_is_multicode"].sum()),
        "mean_sample_weight": round(float(frame["sample_weight"].mean()), 4),
        "median_company_code_count": float(frame["company_num_codes"].median()),
    }
