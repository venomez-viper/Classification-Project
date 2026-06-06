"""Build segment-aware Task 2 data — mirrors T1 pattern but for sub-industries.

Reads:
  data/cleaned/task2_clean.csv   (CompanyId, SegmentName, SegmentDescription, Subindustry)
  llm_finetuning/data/task2_train.csv  (text, label_idx, sub_code)
  llm_finetuning/data/task2_test.csv

Writes:
  llm_finetuning/data/segment_aware_task2/task2_train.csv
  llm_finetuning/data/segment_aware_task2/task2_test.csv

Schema added:
  CompanyId, sub_code, industry_code (1st 8 digits), sector_code, group_code,
  text_primary (segment name + description), text_joint (== text from raw split),
  sample_weight, company_is_multicode, company_num_codes, company_dominant_share,
  row_is_ambiguous_supervision
"""
import re
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CLEAN = ROOT / "data" / "cleaned" / "task2_clean.csv"
SPLIT_DIR = ROOT / "llm_finetuning" / "data"
OUT_DIR = SPLIT_DIR / "segment_aware_task2"
OUT_DIR.mkdir(exist_ok=True)


def norm_subcode(v):
    if pd.isna(v):
        return ""
    s = str(v).strip()
    if s.endswith(".0"):
        s = s[:-2]
    digits = "".join(ch for ch in s if ch.isdigit())
    return digits.zfill(11) if digits else ""


def main():
    print(f"Loading {CLEAN}")
    clean = pd.read_csv(CLEAN)
    clean["sub_code"] = clean["Subindustry"].map(norm_subcode)
    clean = clean[clean["sub_code"] != ""].copy()
    clean["industry_code"] = clean["sub_code"].str[:8]
    clean["lp200"] = (
        clean["SegmentName"].fillna("").astype(str).str.strip()
        + " "
        + clean["SegmentDescription"].fillna("").astype(str).str.strip()
    ).str.replace(r"\s+", " ", regex=True).str[:200]
    print(f"  clean: {len(clean)} rows, {clean['CompanyId'].nunique()} companies, "
          f"{clean['sub_code'].nunique()} sub-industries")

    # Build company profile
    co_grp = clean.groupby("CompanyId")
    co_profile = co_grp.agg(
        company_num_codes=("sub_code", "nunique"),
        company_row_count=("sub_code", "count"),
        company_dominant_code=("sub_code", lambda x: x.value_counts().index[0]),
    )
    co_profile["company_is_multicode"] = (co_profile["company_num_codes"] > 1).astype(int)
    co_profile["company_dominant_share"] = (
        co_grp["sub_code"].apply(lambda x: x.value_counts().iloc[0] / len(x))
    )
    print(f"  multi-code companies: {co_profile['company_is_multicode'].sum()}/{len(co_profile)}")

    for split_name in ("task2_train.csv", "task2_test.csv"):
        in_path = SPLIT_DIR / split_name
        df = pd.read_csv(in_path)
        n = len(df)
        df["sub_code"] = df["sub_code"].map(norm_subcode)
        df["industry_code"] = df["sub_code"].str[:8]
        df["sector_code"] = df["sub_code"].str[:3]
        df["group_code"] = df["sub_code"].str[:5]

        # Join to clean by (text prefix, sub_code) — text in split is segment text
        df["lp200"] = df["text"].fillna("").astype(str).str[:200]
        # Map (lp200, sub_code) -> CompanyId via clean
        clean_lookup = clean.set_index(["lp200", "sub_code"])["CompanyId"].to_dict()
        df["CompanyId"] = df.apply(
            lambda r: clean_lookup.get((r["lp200"], r["sub_code"])), axis=1
        )
        # Fallback by lp200 only
        lp200_to_co = clean.groupby("lp200")["CompanyId"].apply(
            lambda x: x.iloc[0] if x.nunique() == 1 else None
        )
        miss = df["CompanyId"].isna()
        df.loc[miss, "CompanyId"] = df.loc[miss, "lp200"].map(lp200_to_co)

        matched = df["CompanyId"].notna().sum()
        print(f"\n{split_name}: {matched}/{n} CompanyId matched ({matched/n*100:.1f}%)")

        # Attach company profile
        df = df.merge(co_profile.reset_index(), on="CompanyId", how="left")
        df["company_is_multicode"] = df["company_is_multicode"].fillna(0).astype(int)
        df["company_num_codes"] = df["company_num_codes"].fillna(1).astype(int)
        df["company_dominant_share"] = df["company_dominant_share"].fillna(1.0)
        df["row_is_ambiguous_supervision"] = df["company_is_multicode"]

        # Sample weight (no revenue_share for T2 — coarser)
        # Multi-code: 0.7x. Dominant-share rows for multi-code: 0.85. Single-code: 1.15.
        sw = np.where(df["company_is_multicode"] == 1, 0.70, 1.15)
        # Lift dominant rows in multi-code companies
        is_dominant = (df["sub_code"] == df["company_dominant_code"]).astype(float)
        sw = sw * np.where((df["company_is_multicode"] == 1) & (is_dominant == 1), 1.20, 1.0)
        df["sample_weight"] = np.clip(sw, 0.20, 1.75)

        # text_primary == text (T2 split file already IS segment-only)
        df["text_primary"] = df["text"]
        df["text_joint"] = df["text"]  # no LongProfile to add for T2
        df["code"] = df["sub_code"]

        # Reorder + save
        out_cols = [
            "CompanyId", "code", "sub_code", "industry_code", "sector_code", "group_code",
            "label_idx", "text_primary", "text_joint", "text",
            "sample_weight", "row_is_ambiguous_supervision",
            "company_is_multicode", "company_num_codes", "company_dominant_share",
        ]
        out = df[out_cols].copy()
        out_path = OUT_DIR / split_name
        out.to_csv(out_path, index=False)
        print(f"  wrote {out_path}  shape={out.shape}")
        print(f"    sample_weight mean={out['sample_weight'].mean():.3f}  "
              f"ambiguous={out['row_is_ambiguous_supervision'].sum()}")


if __name__ == "__main__":
    main()
