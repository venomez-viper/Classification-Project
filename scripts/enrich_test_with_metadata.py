"""Enrich task1_test.csv with CompanyId, revenue_share, is_largest_share_segment.

Joins task1_test.csv (text, label_idx, mstar_code) back to data/cleaned/task1_clean.csv
via LongProfile prefix matching, then attaches segment-level metadata for the matching
(CompanyId, mstar_code) pair using SegmentDescription substring presence.

Outputs:
  llm_finetuning/data/task1_test_enriched.csv
  llm_finetuning/data/task1_train_enriched.csv

Schema:
  text, label_idx, mstar_code, CompanyId, n_codes_for_company,
  revenue_share, is_largest_share_segment, company_kind
where company_kind in {single_code, multi_code}.
"""
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLEAN = ROOT / "data" / "cleaned" / "task1_clean.csv"
SPLIT_DIR = ROOT / "llm_finetuning" / "data"


def build_lp_to_company(clean: pd.DataFrame) -> dict:
    """LongProfile prefix → CompanyId (only when prefix is unique to one company)."""
    out = {}
    for prefix_len in (200, 100, 50):
        clean[f"_lp{prefix_len}"] = (
            clean["LongProfile"].fillna("").astype(str).str[:prefix_len]
        )
        grp = clean.groupby(f"_lp{prefix_len}")["CompanyId"].apply(
            lambda x: x.iloc[0] if x.nunique() == 1 else None
        )
        out[prefix_len] = grp.dropna().to_dict()
    return out


def enrich(split_csv: Path, lp_maps: dict, clean: pd.DataFrame) -> pd.DataFrame:
    df = pd.read_csv(split_csv)
    n = len(df)

    # Pass 1: assign CompanyId via prefix lookup
    company_ids = []
    for txt in df["text"].astype(str):
        cid = lp_maps[200].get(txt[:200])
        if cid is None:
            cid = lp_maps[100].get(txt[:100])
        if cid is None:
            cid = lp_maps[50].get(txt[:50])
        company_ids.append(cid)
    df["CompanyId"] = company_ids

    # Pass 2: attach segment-level metadata where text contains SegmentDescription
    # Build (CompanyId, mstar_code) -> list of clean row indices
    clean_grp = clean.groupby(["CompanyId", "MstarGlobal"]).indices

    rev_share = []
    is_largest = []
    for i, row in df.iterrows():
        cid, code = row["CompanyId"], row["mstar_code"]
        rs, il = None, None
        if cid is not None and (cid, code) in clean_grp:
            candidates = clean_grp[(cid, code)]
            text = str(row["text"])
            picked = None
            if len(candidates) == 1:
                picked = candidates[0]
            else:
                for c_idx in candidates:
                    sd = str(clean.iloc[c_idx]["SegmentDescription"]) if pd.notna(
                        clean.iloc[c_idx]["SegmentDescription"]
                    ) else ""
                    if len(sd) > 30 and sd[:80] in text:
                        picked = c_idx
                        break
                if picked is None:
                    # Fallback: take the largest-share segment for this (company, code)
                    largest = [
                        c
                        for c in candidates
                        if clean.iloc[c]["is_largest_share_segment"]
                    ]
                    picked = (largest or candidates)[0]
            rs = clean.iloc[picked]["revenue_share"]
            il = bool(clean.iloc[picked]["is_largest_share_segment"])
        rev_share.append(rs)
        is_largest.append(il)

    df["revenue_share"] = rev_share
    df["is_largest_share_segment"] = is_largest

    # Pass 3: company kind
    codes_per_co = clean.groupby("CompanyId")["MstarGlobal"].nunique()
    df["n_codes_for_company"] = df["CompanyId"].map(codes_per_co)
    df["company_kind"] = df["n_codes_for_company"].apply(
        lambda x: "single_code" if x == 1 else ("multi_code" if x and x > 1 else "unknown")
    )

    matched = df["CompanyId"].notna().sum()
    print(f"  {split_csv.name}: {matched}/{n} CompanyId matched ({matched/n*100:.1f}%)")
    print(f"    revenue_share filled: {df['revenue_share'].notna().sum()}")
    print(f"    is_largest filled:    {df['is_largest_share_segment'].notna().sum()}")
    print(f"    single_code rows: {(df['company_kind']=='single_code').sum()}")
    print(f"    multi_code  rows: {(df['company_kind']=='multi_code').sum()}")
    print(f"    unknown     rows: {(df['company_kind']=='unknown').sum()}")
    return df


def main():
    print(f"Loading clean: {CLEAN}")
    clean = pd.read_csv(CLEAN)
    print(f"  {len(clean)} rows, {clean['CompanyId'].nunique()} companies")

    print("\nBuilding LongProfile prefix → CompanyId maps")
    lp_maps = build_lp_to_company(clean)
    for k, v in lp_maps.items():
        print(f"  prefix {k}: {len(v)} unique entries")

    for split in ("task1_test.csv", "task1_train.csv"):
        in_path = SPLIT_DIR / split
        out_path = SPLIT_DIR / split.replace(".csv", "_enriched.csv")
        print(f"\nEnriching {split}")
        out = enrich(in_path, lp_maps, clean)
        out.to_csv(out_path, index=False)
        print(f"  wrote {out_path}")


if __name__ == "__main__":
    main()
