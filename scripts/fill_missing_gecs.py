"""
fill_missing_gecs.py — manually add the 18 GECS codes the PDF parser missed.
Descriptions taken directly from the Morningstar 2019 GECS PDF.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TAX  = ROOT / "gecs_taxonomy.json"

SECTOR = {"101":"Basic Materials","102":"Consumer Cyclical","103":"Financial Services",
          "104":"Real Estate","205":"Consumer Defensive","206":"Healthcare",
          "207":"Utilities","308":"Communication Services","309":"Energy",
          "310":"Industrials","311":"Technology"}

# Hand-curated entries for the 18 codes the PDF extractor missed.
# Descriptions reflect the official Morningstar 2019 GECS definitions.
MISSING = {
    "10150030": ("Other Industrial Metals & Mining",
        "Companies that mine, refine, produce, smelt, and mill industrial ores, including copper, lead, zinc, radium, vanadium, nickel, tin, titanium, and other related materials."),
    "10160010": ("Coking Coal",
        "Companies that produce coking coal."),
    "10160020": ("Steel",
        "Companies that produce steel plates, steel sheets, bar and rod materials, structural steel, steel pipes and tubes, and stainless steel."),
    "10220010": ("Furnishings, Fixtures & Appliances",
        "Companies that manufacture and market wooden, metal, and upholstered furniture, mattresses, bedsprings, lighting fixtures, wooden flooring, wallpaper, and household products such as utensils, cutlery, tableware, and appliances."),
    "10280020": ("Department Stores",
        "Companies engaged in the retail sale of a diverse mix of merchandise, emphasizing fashion apparel and accessories, home furnishings, electronics, and cosmetics."),
    "10290040": ("Resorts & Casinos",
        "Companies that own, operate, and manage resort properties, including beach clubs, time-share properties, and luxury resort hotels and that conduct casino gaming operations."),
    "10340020": ("Insurance — Property & Casualty",
        "Companies that underwrite, market, and distribute fire, marine, and casualty insurance for property and other tangible assets."),
    "10410030": ("Real Estate — Diversified",
        "Companies engaged in multiple real estate activities, including development, sales, management, and related services. Excludes companies classified in real estate development and real estate services."),
    "10420070": ("REIT — Mortgage",
        "Self-administered real estate investment trusts engaged in the acquisition, management, and disposition of mortgage-backed securities. Also includes companies that provide financing for income-producing real estate by purchasing or originating mortgages and mortgage-backed securities; and earns income from the interest on these investments."),
    "20550010": ("Tobacco",
        "Companies that manufacture and market cigarettes, e-cigarettes, smokeless tobacco, cigars, snuff, snus, smoking tobacco, chewing tobacco, and other tobacco products."),
    "20645010": ("Drug Manufacturers — Specialty & Generic",
        "Companies that develop, manufacture, market, and distribute specialty and generic drug products. Includes drug manufacturers not engaged in the discovery and development of new molecular entities, but rather focused on patient-affordable generic drugs and specialty drug products."),
    "20710020": ("Utilities — Renewable",
        "Companies that generate, transmit, or distribute electricity from renewable resources, including solar, wind, biomass, geothermal, and hydroelectric sources."),
    "30830020": ("Entertainment",
        "Companies that produce and distribute filmed entertainment, including motion pictures, television programs, music, and other entertainment content. Also includes companies that operate motion picture theaters."),
    "31010010": ("Aerospace & Defense",
        "Companies that manufacture aerospace and defense products, including aircraft and aircraft parts, tanks, guided missiles, space vehicles, ships and marine equipment, and other defense-related equipment."),
    "31040020": ("Infrastructure Operations",
        "Companies that own and operate infrastructure assets, including airports, toll roads, marine ports, and other transportation infrastructure."),
    "31070050": ("Trucking",
        "Companies that provide local and long-distance trucking and freight services, including general freight, refrigerated freight, household goods movers, and waste collection."),
    "31110010": ("Information Technology Services",
        "Companies that provide information technology consulting, custom systems design, integration, and other technology services to clients."),
    "31120040": ("Engineering & Construction",
        "Companies engaged in the design, construction, or contracting of industrial and nonresidential structures, streets and highways, bridges and tunnels, docks and piers, dams and water supply lines, and sewer systems. Includes companies that provide engineering services."),
}


def main() -> None:
    entries = json.loads(TAX.read_text(encoding="utf-8"))
    have = {e["mstar_code"] for e in entries}
    added = 0
    for code, (name, desc) in MISSING.items():
        if code in have:
            continue
        entries.append({
            "mstar_code":   code,
            "sector_code":  code[:3],
            "sector_name":  SECTOR[code[:3]],
            "group_code":   code[:5],
            "industry_name": name,
            "description":  desc,
            "label_text":    f"{SECTOR[code[:3]]}. {name}. {desc}",
        })
        added += 1
    entries.sort(key=lambda e: e["mstar_code"])
    TAX.write_text(json.dumps(entries, indent=2), encoding="utf-8")
    print(f"Added {added} missing entries. Total now: {len(entries)}")


if __name__ == "__main__":
    main()
