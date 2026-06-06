"""
parse_gecs_taxonomy.py — minimal version that just works.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pdfplumber

ROOT = Path(__file__).resolve().parents[1]
PDF  = ROOT / "Task Doc/MorningstarGlobalEquityClassStructure2019v2.pdf"
OUT  = ROOT / "gecs_taxonomy.json"

SECTOR_NAMES = {
    "101": "Basic Materials",          "102": "Consumer Cyclical",
    "103": "Financial Services",       "104": "Real Estate",
    "205": "Consumer Defensive",       "206": "Healthcare",
    "207": "Utilities",                "308": "Communication Services",
    "309": "Energy",                   "310": "Industrials",
    "311": "Technology",
}
VALID = set(SECTOR_NAMES.keys())


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    with pdfplumber.open(str(PDF)) as pdf:
        full = "\n".join(p.extract_text() or "" for p in pdf.pages[9:])

    # Strip page footers/numbers (NON-greedy, single-line scope only)
    lines = full.split("\n")
    keep = []
    skip_next = 0
    for ln in lines:
        s = ln.strip()
        if skip_next > 0:
            skip_next -= 1
            continue
        if "©" in s and "Morningstar" in s:
            skip_next = 2  # skip "©... rights reserved", "in whole or in part...", footer
            continue
        if "The Morningstar Global Equity" in s:
            continue
        if re.fullmatch(r"\d{1,3}", s):  # standalone page number
            continue
        if "Reproduction or transcription" in s:
            continue
        keep.append(ln)
    full = "\n".join(keep)

    # Find all 8-digit codes (anywhere) and keep only valid GECS ones
    matches = list(re.finditer(r"\b(\d{8})\b", full))
    valid = [m for m in matches if m.group(1)[:3] in VALID]

    entries: dict[str, dict] = {}
    for i, m in enumerate(valid):
        code = m.group(1)
        start = m.end()
        # Take everything up to the NEXT valid code
        end = valid[i + 1].start() if i + 1 < len(valid) else len(full)
        chunk = full[start:end]
        # Drop leading 5-digit group codes that may appear (like "10120")
        chunk = re.sub(r"^[\s\n]*\d{5}\s*\n", "\n", chunk)
        chunk = chunk.strip()
        # First non-empty line = industry name, rest = description
        lines = [l.strip() for l in chunk.split("\n") if l.strip()]
        if not lines:
            continue
        name = lines[0]
        # Subsequent lines: description until end (could span pages)
        description = " ".join(lines[1:])
        description = re.sub(r"\s+", " ", description).strip()
        # Truncate description at obvious cutoffs (next group code header)
        description = re.sub(r"\s+\d{5}\s+$", "", description)
        # Keep longest description per code
        if code not in entries or len(description) > len(entries[code]["description"]):
            entries[code] = {
                "mstar_code":   code,
                "sector_code":  code[:3],
                "sector_name":  SECTOR_NAMES[code[:3]],
                "group_code":   code[:5],
                "industry_name": name,
                "description":  description,
                "label_text":    f"{SECTOR_NAMES[code[:3]]}. {name}. {description}",
            }

    final = sorted(entries.values(), key=lambda x: x["mstar_code"])
    OUT.write_text(json.dumps(final, indent=2), encoding="utf-8")
    print(f"Extracted {len(final)} unique GECS codes", flush=True)
    # Show first 3 + a random middle one + last
    for e in [final[0], final[len(final)//3], final[2*len(final)//3], final[-1]]:
        print(f"\n  {e['mstar_code']} [{e['sector_name']}] {e['industry_name'][:50]}")
        print(f"    {e['description'][:160]}")


if __name__ == "__main__":
    main()
