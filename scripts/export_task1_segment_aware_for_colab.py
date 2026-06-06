from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task1_segment_aware_common import build_task1_segment_aware_splits, save_json


OUT_DIR = ROOT / "llm_finetuning" / "data" / "segment_aware_task1"


def encode_map(values: pd.Series) -> tuple[pd.Series, dict[str, int], dict[int, str]]:
    classes = sorted(values.astype(str).unique().tolist())
    code_to_idx = {code: idx for idx, code in enumerate(classes)}
    idx_to_code = {idx: code for code, idx in code_to_idx.items()}
    return values.astype(str).map(code_to_idx), code_to_idx, idx_to_code


def prepare_frame(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, dict]]:
    out = frame.copy()
    out["text_primary"] = out["segment_text"].astype(str)
    out["text_aux"] = out["company_text"].astype(str)
    out["text_joint"] = (
        out["text_primary"].astype(str).str.strip()
        + " [COMPANY] "
        + out["text_aux"].astype(str).str.strip()
    ).str.replace(r"\s+", " ", regex=True).str.strip()

    out["label_idx"], mstar_code_to_idx, mstar_idx_to_code = encode_map(out["code"])
    out["sector_idx"], sector_code_to_idx, sector_idx_to_code = encode_map(out["sector_code"])
    out["group_idx"], group_code_to_idx, group_idx_to_code = encode_map(out["group_code"])

    keep_cols = [
        "CompanyId",
        "code",
        "sector_code",
        "group_code",
        "label_idx",
        "sector_idx",
        "group_idx",
        "text_primary",
        "text_aux",
        "text_joint",
        "sample_weight",
        "row_is_ambiguous_supervision",
        "company_is_multicode",
        "company_num_codes",
        "company_dominant_share",
        "longprofile_is_ambiguous",
        "row_matches_company_dominant",
        "row_matches_longprofile_dominant",
    ]
    maps = {
        "mstar_code_to_idx": mstar_code_to_idx,
        "mstar_idx_to_code": mstar_idx_to_code,
        "sector_code_to_idx": sector_code_to_idx,
        "sector_idx_to_code": sector_idx_to_code,
        "group_code_to_idx": group_code_to_idx,
        "group_idx_to_code": group_idx_to_code,
    }
    return out[keep_cols].copy(), maps


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    train, test, summary = build_task1_segment_aware_splits()

    train_out, train_maps = prepare_frame(train)
    test_out, test_maps = prepare_frame(test)

    # Align test indices to train mappings
    test_out["label_idx"] = test_out["code"].astype(str).map(train_maps["mstar_code_to_idx"])
    test_out["sector_idx"] = test_out["sector_code"].astype(str).map(train_maps["sector_code_to_idx"])
    test_out["group_idx"] = test_out["group_code"].astype(str).map(train_maps["group_code_to_idx"])

    train_out.to_csv(OUT_DIR / "task1_segment_aware_train.csv", index=False)
    test_out.to_csv(OUT_DIR / "task1_segment_aware_test.csv", index=False)

    maps = {**train_maps, "summary": summary}
    save_json(maps, OUT_DIR / "task1_segment_aware_label_maps.json")

    manifest = {
        "train_csv": str((OUT_DIR / "task1_segment_aware_train.csv").relative_to(ROOT)),
        "test_csv": str((OUT_DIR / "task1_segment_aware_test.csv").relative_to(ROOT)),
        "label_maps_json": str((OUT_DIR / "task1_segment_aware_label_maps.json").relative_to(ROOT)),
        "text_fields": {
            "primary": "text_primary",
            "auxiliary": "text_aux",
            "joint": "text_joint",
        },
        "targets": {
            "industry": "label_idx",
            "sector": "sector_idx",
            "group": "group_idx",
        },
        "recommendation": {
            "first_run": "text_joint",
            "ablation_run": "text_primary",
            "sample_weight_column": "sample_weight",
        },
    }
    save_json(manifest, OUT_DIR / "task1_segment_aware_manifest.json")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
