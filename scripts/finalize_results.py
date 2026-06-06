"""
finalize_results.py
===================
Reads all V*/models_v*/training_summary.json files, ranks them, picks
the winner, and appends results to CASCADE_AUDIT.md plus writes a
new RESULTS.md.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CANDIDATES = [
    ("V2 (cascade, V3 features, CompanyId split)", ROOT / "models_v2" / "cascade_training_summary.json"),
    ("V4 (MiniLM embeddings, row-level)",            ROOT / "models_v4" / "training_summary.json"),
    ("V5 (hybrid TF-IDF + MiniLM)",                  ROOT / "models_v5" / "training_summary.json"),
    ("V6 (hybrid TF-IDF + BGE-base)",                ROOT / "models_v6" / "training_summary.json"),
    ("V7 (SetFit fine-tune + classifier)",           ROOT / "models_v7" / "training_summary.json"),
    ("V8 (mega-ensemble of all encoders + TF-IDF)",  ROOT / "models_v8" / "training_summary.json"),
]


def get_f1(summary: dict) -> float | None:
    for k in ("macro_f1", "best_f1", "f1"):
        if k in summary:
            v = summary[k]
            return v / 100 if v > 1.5 else v
    return None


def get_top10(summary: dict) -> int | None:
    for k in ("top10_pass", "flat_top10_pass", "cascade_top10_pass"):
        if k in summary:
            return summary[k]
    return None


def main() -> None:
    rows = []
    for label, path in CANDIDATES:
        if not path.exists():
            rows.append((label, None, None, "missing", path))
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            rows.append((label, None, None, f"error: {exc}", path))
            continue
        f1 = get_f1(data)
        top10 = get_top10(data)
        rows.append((label, f1, top10, data, path))

    # Rank by F1 (descending), missing/error at bottom
    valid = [r for r in rows if isinstance(r[1], float)]
    invalid = [r for r in rows if not isinstance(r[1], float)]
    valid.sort(key=lambda r: -r[1])
    rows = valid + invalid

    print("=" * 70)
    print("FINAL RESULTS — Task 1 GECS Industry Classification")
    print("=" * 70)
    for label, f1, top10, data, path in rows:
        if isinstance(f1, float):
            target = "PASS" if f1 >= 0.75 else "FAIL"
            t10str = f"{top10}/10" if top10 is not None else "—"
            print(f"  {label:50s}  F1={f1*100:6.2f}%  top10={t10str}  [{target}]")
        else:
            print(f"  {label:50s}  ({data})")
    print("=" * 70)

    if valid:
        winner_label, winner_f1, winner_top10, winner_data, _ = valid[0]
        target = "PASS" if winner_f1 >= 0.75 else "FAIL"
        print(f"\nWinner: {winner_label}")
        print(f"  Macro F1   : {winner_f1*100:.2f}%")
        print(f"  Top-10 pass: {winner_top10}/10")
        print(f"  Target &gt;=75%: {target}")
    else:
        winner_label = winner_f1 = winner_top10 = None
        print("\nNo successful runs.")

    # Write RESULTS.md
    md = ["# Task 1 — Final Results\n",
          "All evaluated on the case-standard row-level 80/20 split",
          "(`task1_train.csv` -&gt; `task1_test.csv`).\n",
          "## Leaderboard\n",
          "| Rank | Approach | Macro F1 | Top-10 pass | Target &gt;=75% |",
          "|---|---|---|---|---|"]
    for i, (label, f1, top10, _, _) in enumerate(rows):
        if isinstance(f1, float):
            t = "PASS" if f1 >= 0.75 else "FAIL"
            t10str = f"{top10}/10" if top10 is not None else "—"
            md.append(f"| {i+1} | {label} | {f1*100:.2f}% | {t10str} | {t} |")
        else:
            md.append(f"| — | {label} | not run | — | — |")

    if valid:
        md.append("\n## Winner\n")
        md.append(f"**{winner_label}** — Macro F1 {winner_f1*100:.2f}% — top-10 {winner_top10}/10")
        if winner_f1 >= 0.75:
            md.append(f"\n[PASS] Clears case requirement of &gt;=75% Macro F1.")
        else:
            md.append(f"\n[FAIL] Below case requirement of &gt;=75% Macro F1 (gap: {(0.75-winner_f1)*100:.2f}pp).")
        md.append(f"\n### Winner config\n```json")
        md.append(json.dumps(winner_data, indent=2))
        md.append("```\n")

    md.append("\n## Audit history\n")
    md.append("See [`CASCADE_AUDIT.md`](CASCADE_AUDIT.md) for full chronological")
    md.append("record of problems found, fixes applied, and methodology.\n")

    (ROOT / "RESULTS.md").write_text("\n".join(md), encoding="utf-8")
    print(f"\nWrote RESULTS.md")

    # Append final block to CASCADE_AUDIT.md
    audit = ROOT / "CASCADE_AUDIT.md"
    if audit.exists():
        text = audit.read_text(encoding="utf-8")
        marker = "\n\n## 7. Final Results (auto-generated)\n"
        if marker in text:
            text = text.split(marker)[0]
        block = [marker]
        block.append("All evaluated on `task1_test.csv` after training on `task1_train.csv`.\n")
        block.append("| Approach | F1 | Top-10 | Status |")
        block.append("|---|---|---|---|")
        for label, f1, top10, _, _ in rows:
            if isinstance(f1, float):
                t = "PASS" if f1 >= 0.75 else "FAIL"
                t10str = f"{top10}/10" if top10 is not None else "—"
                block.append(f"| {label} | {f1*100:.2f}% | {t10str} | {t} |")
            else:
                block.append(f"| {label} | (not run) | — | — |")
        if valid:
            block.append(f"\n**Winner:** {winner_label} — **{winner_f1*100:.2f}%** "
                         f"({'&gt;=75% PASS' if winner_f1 >= 0.75 else f'gap to 75%: {(0.75-winner_f1)*100:.2f}pp'})\n")
        audit.write_text(text + "\n" + "\n".join(block) + "\n", encoding="utf-8")
        print(f"Appended results block to CASCADE_AUDIT.md")


if __name__ == "__main__":
    main()
