from __future__ import annotations

import re
from typing import Iterable


STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in", "into",
    "is", "it", "its", "of", "on", "or", "that", "the", "their", "this", "to",
    "with", "company", "segment", "services", "products", "provides", "includes",
}

SECTOR_NEIGHBORS = {
    "Regional Banks": "Diversified Banks and Capital Markets",
    "Diversified Banks": "Regional Banks and Capital Markets",
    "Capital Markets": "Asset Management and Diversified Financial Services",
    "Asset Management": "Capital Markets and Diversified Financial Services",
    "Biotechnology": "Drug Manufacturers and Medical Devices",
    "Drug Manufacturers - General": "Biotechnology and Specialty Pharmaceuticals",
    "Medical Devices": "Medical Instruments & Supplies and Healthcare Technology",
    "Software - Application": "Software - Infrastructure and IT Services & Cloud Computing",
    "Software - Infrastructure": "IT Services & Cloud Computing and Software - Application",
    "Semiconductors": "Semiconductor Equipment and Electronic Components",
    "Aerospace & Defense": "Industrial Machinery and Diversified Industrials",
    "Oil & Gas E&P": "Oil & Gas Integrated and Oil & Gas Midstream",
    "Oil & Gas Midstream": "Oil & Gas E&P and Oil & Gas Equipment & Services",
}


def extract_evidence_phrases(text: str, limit: int = 3) -> list[str]:
    chunks = re.split(r"[.;:\n]+", text)
    scored = []
    for chunk in chunks:
        cleaned = chunk.strip()
        if len(cleaned.split()) < 3:
            continue
        tokens = re.findall(r"[A-Za-z][A-Za-z\-]{2,}", cleaned.lower())
        informative = [t for t in tokens if t not in STOPWORDS]
        score = len(set(informative))
        if score:
            scored.append((score, cleaned))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [chunk for _, chunk in scored[:limit]]


def generate_explanation(text: str, label: str, code: str, engine: str) -> dict[str, str]:
    evidence: list[str] = extract_evidence_phrases(text)
    memo = _build_memo(label, code, engine, evidence)
    return {"engine": "HeuristicMemo", "text": memo}


def _build_memo(label: str, code: str, engine: str, evidence: Iterable[str]) -> str:
    evidence = [piece.strip() for piece in evidence if piece.strip()]
    neighbors = SECTOR_NEIGHBORS.get(label, "adjacent sectors")

    if evidence:
        primary = evidence[0]
        secondary = evidence[1] if len(evidence) > 1 else None
        cite = f'"{primary}"'
        if secondary:
            cite += f' and "{secondary}"'
        return (
            f"{label} ({code}) is the best-fit classification because the business profile "
            f"centers on {cite} — language strongly associated with this industry's operating model. "
            f"This distinguishes the company from {neighbors}, where those revenue drivers are absent. "
            f"Classification served by {engine}."
        )

    return (
        f"{label} ({code}) is the best-fit classification based on the overall vocabulary, "
        f"operating focus, and business context of the description. "
        f"The profile aligns more closely with this sector than with {neighbors}. "
        f"Classification served by {engine}."
    )
