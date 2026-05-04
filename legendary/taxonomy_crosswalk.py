from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from legendary.shared import get_label, normalize_code


DEFAULT_CROSSWALK_PATH = Path("legendary_artifacts/taxonomy_crosswalk.json")


def load_crosswalk(path: str | Path = DEFAULT_CROSSWALK_PATH) -> dict[str, Any]:
    path = Path(path)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _fallback_crosswalk(code: str) -> dict[str, Any]:
    code = normalize_code(code)
    label = get_label(code)
    return {
        "mstar": {"code": code, "label": label},
        "gics": {"code": "", "label": "Pending mapping"},
        "naics": {"code": "", "label": "Pending mapping"},
        "sic": {"code": "", "label": "Pending mapping"},
        "status": "starter-template",
    }


def get_cross_taxonomy(code: str, crosswalk: dict[str, Any] | None = None) -> dict[str, Any]:
    code = normalize_code(code)
    crosswalk = crosswalk or {}
    if code in crosswalk:
        payload = dict(crosswalk[code])
        payload.setdefault("mstar", {"code": code, "label": get_label(code)})
        payload.setdefault("status", "mapped")
        return payload
    return _fallback_crosswalk(code)
