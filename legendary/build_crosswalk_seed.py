from __future__ import annotations

import json
from pathlib import Path

from legendary.shared import get_label


OUTPUT_PATH = Path("legendary_artifacts/taxonomy_crosswalk.json")


SEED = {
    "10320020": {
        "mstar": {"code": "10320020", "label": get_label("10320020")},
        "gics": {"code": "40101015", "label": "Regional Banks"},
        "naics": {"code": "522110", "label": "Commercial Banking"},
        "sic": {"code": "6021", "label": "National Commercial Banks"},
    },
    "30820020": {
        "mstar": {"code": "30820020", "label": get_label("30820020")},
        "gics": {"code": "45103010", "label": "Application Software"},
        "naics": {"code": "513210", "label": "Software Publishers"},
        "sic": {"code": "7372", "label": "Prepackaged Software"},
    },
    "31130010": {
        "mstar": {"code": "31130010", "label": get_label("31130010")},
        "gics": {"code": "45301020", "label": "Semiconductors"},
        "naics": {"code": "334413", "label": "Semiconductor and Related Device Manufacturing"},
        "sic": {"code": "3674", "label": "Semiconductors and Related Devices"},
    },
}


def main() -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(SEED, indent=2), encoding="utf-8")
    print(f"Crosswalk seed saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
