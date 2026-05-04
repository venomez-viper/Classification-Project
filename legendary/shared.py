from __future__ import annotations

from typing import Any


MSTAR_LABELS = {
    "10110010": "Oil & Gas Integrated",
    "10110020": "Oil & Gas E&P",
    "10110030": "Oil & Gas Midstream",
    "10130020": "Agricultural Inputs",
    "10200010": "Auto & Truck Dealerships",
    "10310010": "Diversified Financial Services",
    "10310015": "Diversified Chemicals",
    "10310020": "Engineering & Construction",
    "10320010": "Capital Markets",
    "10320020": "Regional Banks",
    "10320030": "Diversified Banks",
    "10320040": "Insurance - Life & Health",
    "10320050": "Insurance - Property & Casualty",
    "10340010": "Asset Management",
    "10340060": "Insurance - Multi-line",
    "10420020": "Building Products & Equipment",
    "20524010": "Healthcare Plans",
    "20525010": "Medical Care Facilities",
    "20525040": "Packaged Foods",
    "20527010": "Drug Manufacturers - General",
    "20527020": "Biotechnology",
    "20527050": "Drug Manufacturers - Specialty & Generic",
    "20528010": "Medical Devices",
    "20528020": "Medical Instruments & Supplies",
    "20645030": "Healthcare Technology",
    "20650010": "Medical Equipment & Instruments",
    "30810010": "Electronic Components",
    "30810020": "Electronic Manufacturing Services",
    "30810030": "Telecom Services",
    "30820010": "Internet Content & Information",
    "30820020": "Software - Application",
    "30820030": "Software - Infrastructure",
    "30830010": "Internet Search & AI Services",
    "30830020": "Entertainment",
    "30830030": "Broadcasting & Media",
    "30910020": "Oil & Gas Equipment & Services",
    "31020010": "Aerospace & Defense",
    "31020020": "Industrial Machinery",
    "31020030": "Diversified Industrials",
    "31110020": "Software - Security",
    "31110030": "IT Services & Cloud Computing",
    "31120020": "Electrical Equipment & Parts",
    "31120040": "Optical Components & Imaging",
    "31120060": "Scientific & Technical Instruments",
    "31130010": "Semiconductors",
    "31130020": "Semiconductor Equipment",
}


PREFIX_LABELS = {
    "101": "Energy & Extraction",
    "102": "Basic Materials & Consumer",
    "103": "Financial Services",
    "104": "Real Estate / Construction",
    "205": "Healthcare & Pharma",
    "206": "Medical Equipment",
    "207": "Healthcare Services",
    "210": "Consumer Retail",
    "306": "Real Estate (REIT)",
    "308": "Technology & Communications",
    "309": "Energy Equipment",
    "310": "Industrials & Manufacturing",
    "311": "IT & Semiconductors",
}


def normalize_code(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if not text:
        return ""
    if text.endswith(".0"):
        text = text[:-2]
    digits = "".join(ch for ch in text if ch.isdigit())
    return digits.zfill(8) if digits else ""


def get_label(code: str) -> str:
    code = normalize_code(code)
    if code in MSTAR_LABELS:
        return MSTAR_LABELS[code]
    prefix = code[:3]
    broad_sector = PREFIX_LABELS.get(prefix, "Miscellaneous Industry")
    return f"{broad_sector} (Code: {code})"


def make_prediction_payload(code: str) -> dict[str, str]:
    code = normalize_code(code)
    return {
        "mstar_code": code,
        "mstar_label": get_label(code),
        "sector_code": code[:3],
        "sector_label": PREFIX_LABELS.get(code[:3], "Unknown Sector"),
        "group_code": code[:5],
    }
