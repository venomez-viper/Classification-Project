from __future__ import annotations

import csv
import json
import math
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from html import escape
from pathlib import Path
from typing import Iterable
from urllib.parse import quote

import docx
import mistune


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_HTML = ROOT / "team_briefing.html"
BUILD_DATE = "2026-05-14"
PRESENTATION_DATE = "2026-05-18"
CATEGORY_LABELS = {
    "story": "Story Spine",
    "data": "Data",
    "models": "Models",
    "results": "Results",
    "problems": "Problems / Audit",
    "plan": "Plan",
    "team": "Team / Logistics",
    "reference": "Reference",
}

SOURCE_FILES = [
    "README.md",
    "CAPSTONE_FINAL_REPORT.md",
    "PROJECT_JOURNEY.md",
    "CASCADE_AUDIT.md",
    "RESULTS.md",
    "LEGENDARY_ROADMAP.md",
    "WEEK_5_PLAN.md",
    "HANDOFF_PLAYBOOK.md",
    "ENSEMBLE_DOCUMENTATION.md",
    "LLM_EVALUATION_STRATEGY.md",
    "FULL_SYSTEM_REVAMP.md",
    "CONTRIBUTING.md",
    "CODEX_BUILD_TASKS.md",
    "Launch notes.txt",
    "gecs_taxonomy.json",
    "Capstone Week 2 Team Doc.docx",
    "Week3_Team_Classifier_Assignments.docx",
    "overnight_run.log",
    "modernbert_large_v3_test_predictions.csv",
]


@dataclass
class Node:
    node_id: str
    title: str
    category: str
    body_markdown: str
    sources: list[str]
    spine_step: int | None = None
    next_node_id: str | None = None
    story_arc: bool = False
    synthesis_flag: str | None = None
    todos: list[str] | None = None


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def read_docx_text(path: Path) -> str:
    document = docx.Document(path)
    return "\n".join(p.text for p in document.paragraphs if p.text.strip())


def read_sources() -> tuple[dict[str, str], list[tuple[str, str]]]:
    texts: dict[str, str] = {}
    unreadable: list[tuple[str, str]] = []
    for rel in SOURCE_FILES:
        path = ROOT / rel
        try:
            if rel.endswith(".docx"):
                texts[rel] = read_docx_text(path)
            elif rel == "overnight_run.log":
                texts[rel] = "\n".join(read_text(path).splitlines()[-200:])
            elif rel == "modernbert_large_v3_test_predictions.csv":
                rows = []
                with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
                    reader = csv.reader(handle)
                    for idx, row in enumerate(reader):
                        rows.append(row)
                        if idx >= 3:
                            break
                texts[rel] = "\n".join(",".join(r) for r in rows)
            else:
                texts[rel] = read_text(path)
        except Exception as exc:  # pragma: no cover - reporting path
            unreadable.append((rel, str(exc)))
    return texts, unreadable


def count_csv_rows_and_header(path: Path) -> tuple[int, list[str]]:
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader)
        rows = sum(1 for _ in reader)
    return rows, header


def count_nonempty_company_ids(path: Path) -> tuple[int, int]:
    total = 0
    nonempty = 0
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            total += 1
            if (row.get("CompanyId") or "").strip():
                nonempty += 1
    return total, nonempty


def compute_multi_code_stats(path: Path) -> tuple[int, int, int]:
    company_to_codes: dict[str, set[str]] = defaultdict(set)
    row_company_ids: list[str] = []
    with path.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            company_id = (row.get("CompanyId") or "").strip()
            code = (row.get("MstarGlobal") or "").strip()
            if not company_id:
                continue
            company_to_codes[company_id].add(code)
            row_company_ids.append(company_id)
    multi_companies = {cid for cid, codes in company_to_codes.items() if len(codes) > 1}
    multi_rows = sum(1 for cid in row_company_ids if cid in multi_companies)
    return len(company_to_codes), len(multi_companies), multi_rows


def extract_models_dirs() -> list[str]:
    return sorted(p.name for p in ROOT.iterdir() if p.is_dir() and p.name.startswith("models"))


def make_link(rel_path: str) -> str:
    href = (ROOT / rel_path).resolve().as_uri()
    return f'<a href="{href}" target="_blank" rel="noopener">{escape(rel_path)}</a>'


def source_block(sources: Iterable[str]) -> str:
    links = " · ".join(make_link(src) for src in sources)
    return f'<div class="sources"><strong>Source files:</strong> {links}</div>'


def chart_f1_progression() -> str:
    bars = [
        ("TF-IDF", 59.65),
        ("V8", 68.42),
        ("ModernBERT-base", 67.18),
        ("ModernBERT-large", 70.29),
    ]
    min_v = 50
    max_v = 82
    width = 620
    height = 280
    chart_left = 58
    chart_bottom = 220
    chart_top = 30
    bar_w = 92
    gap = 42
    colors = ["#4ea8de", "#5e60ce", "#c77dff", "#f4b942"]

    def y_of(value: float) -> float:
        return chart_bottom - ((value - min_v) / (max_v - min_v)) * (chart_bottom - chart_top)

    parts = [
        f'<svg viewBox="0 0 {width} {height}" class="inline-chart" role="img" aria-label="Task 1 F1 progression bar chart">',
        f'<rect x="0" y="0" width="{width}" height="{height}" rx="18" fill="#101424"/>',
    ]
    for tick in [50, 60, 70, 80]:
        y = y_of(tick)
        parts.append(f'<line x1="{chart_left}" y1="{y:.1f}" x2="{width-24}" y2="{y:.1f}" stroke="#23304a" stroke-width="1.2"/>')
        parts.append(f'<text x="20" y="{y+4:.1f}" fill="#94a3b8" font-size="12">{tick}</text>')
    target_y = y_of(80)
    parts.append(f'<line x1="{chart_left}" y1="{target_y:.1f}" x2="{width-24}" y2="{target_y:.1f}" stroke="#ef4444" stroke-width="2.5" stroke-dasharray="8 6"/>')
    parts.append(f'<text x="{width-114}" y="{target_y-8:.1f}" fill="#fca5a5" font-size="12">80 target</text>')
    for idx, (label, value) in enumerate(bars):
        x = chart_left + 18 + idx * (bar_w + gap)
        y = y_of(value)
        h = chart_bottom - y
        parts.append(f'<rect x="{x}" y="{y:.1f}" width="{bar_w}" height="{h:.1f}" rx="10" fill="{colors[idx]}"/>')
        parts.append(f'<text x="{x + bar_w/2:.1f}" y="{y-10:.1f}" text-anchor="middle" fill="#e2e8f0" font-size="13">{value:.2f}</text>')
        parts.append(f'<text x="{x + bar_w/2:.1f}" y="{chart_bottom+24}" text-anchor="middle" fill="#cbd5e1" font-size="12">{escape(label)}</text>')
    parts.append(f'<text x="{width/2:.1f}" y="20" text-anchor="middle" fill="#f8fafc" font-size="15" font-weight="700">Task 1 Macro F1 Progression</text>')
    parts.append("</svg>")
    return "".join(parts)


def chart_leakage_donut() -> str:
    size = 420
    cx = cy = size / 2
    radius = 132
    stroke = 54
    circumference = 2 * math.pi * radius
    leaked = 97.2
    leaked_len = circumference * leaked / 100
    clean_len = circumference - leaked_len
    return f"""
<svg viewBox="0 0 {size} {size}" class="inline-chart donut-chart" role="img" aria-label="Leakage donut chart">
  <rect x="0" y="0" width="{size}" height="{size}" rx="24" fill="#120f17"/>
  <circle cx="{cx}" cy="{cy}" r="{radius}" fill="none" stroke="#2b2538" stroke-width="{stroke}"/>
  <circle cx="{cx}" cy="{cy}" r="{radius}" fill="none" stroke="#ef4444" stroke-width="{stroke}"
          stroke-linecap="butt" stroke-dasharray="{leaked_len:.2f} {clean_len:.2f}"
          transform="rotate(-90 {cx} {cy})"/>
  <circle cx="{cx}" cy="{cy}" r="{radius}" fill="none" stroke="#38bdf8" stroke-width="{stroke}"
          stroke-dasharray="{clean_len:.2f} {leaked_len:.2f}"
          stroke-dashoffset="{-leaked_len:.2f}"
          transform="rotate(-90 {cx} {cy})"/>
  <text x="{cx}" y="{cy-18}" text-anchor="middle" fill="#f8fafc" font-size="34" font-weight="800">97.2%</text>
  <text x="{cx}" y="{cy+12}" text-anchor="middle" fill="#fca5a5" font-size="14" font-weight="700">of test rows seen in training</text>
  <text x="{cx}" y="{cy+34}" text-anchor="middle" fill="#94a3b8" font-size="12">Leaked 97.2% · Clean 2.8%</text>
  <text x="36" y="{size-30}" fill="#fca5a5" font-size="13">Leaked rows</text>
  <text x="{size-122}" y="{size-30}" fill="#7dd3fc" font-size="13">Clean rows</text>
</svg>
"""


def panel_html(md: mistune.Markdown, body_markdown: str, sources: list[str]) -> str:
    rendered = md(body_markdown)
    return rendered + source_block(sources)


def build_nodes(texts: dict[str, str]) -> tuple[list[Node], dict[str, list[str]]]:
    taxonomy = json.loads(texts["gecs_taxonomy.json"])
    taxonomy_count = len(taxonomy)
    task1_rows, task1_cols = count_csv_rows_and_header(ROOT / "data/cleaned/task1_clean.csv")
    train_total, train_joined = count_nonempty_company_ids(ROOT / "llm_finetuning/data/task1_train_with_companyid.csv")
    test_total, test_joined = count_nonempty_company_ids(ROOT / "llm_finetuning/data/task1_test_with_companyid.csv")
    company_count, multi_company_count, multi_rows = compute_multi_code_stats(ROOT / "data/cleaned/task1_clean.csv")
    model_dirs = extract_models_dirs()

    file_map_lines = [
        "- `README.md` — current public-facing status, serving path, and the honest project narrative.",
        "- `CAPSTONE_FINAL_REPORT.md` — polished final-report draft, but still carries pre-audit 88.90% claims.",
        "- `PROJECT_JOURNEY.md` — the honest iteration log from leaked baseline to rebuilt experiments.",
        "- `CASCADE_AUDIT.md` — the most important methodology record: where leakage happened and what changed.",
        "- `RESULTS.md` — concise Task 1 leaderboard for the classical-model sweep.",
        "- `LEGENDARY_ROADMAP.md` — ambitious product roadmap with several claims that now need cross-checking.",
        "- `WEEK_5_PLAN.md` — the week-five execution plan, owners, gates, and target metrics.",
        "- `HANDOFF_PLAYBOOK.md` — the live handoff and Monday checklist with the strongest pitch language.",
        "- `ENSEMBLE_DOCUMENTATION.md` — why a hybrid ensemble was proposed to handle the 145-class long tail.",
        "- `LLM_EVALUATION_STRATEGY.md` — early DeBERTa evaluation memo explaining macro-F1 pain on rare classes.",
        "- `FULL_SYSTEM_REVAMP.md` — full product/deployment spec for frontend, backend, and HF Space.",
        "- `CONTRIBUTING.md` — repo collaboration conventions, not a project-status document.",
        "- `CODEX_BUILD_TASKS.md` — build backlog for deployment shell, slides, runbook, and README polish.",
        "- `Launch notes.txt` — present but empty; no launch instructions were readable from it.",
        "- `gecs_taxonomy.json` — parsed Morningstar taxonomy with all 145 industry definitions.",
        "- `Capstone Week 2 Team Doc.docx` — early team process, setup, and roster instructions.",
        "- `Week3_Team_Classifier_Assignments.docx` — Week 3 classifier assignments by member number, not by speaker role.",
        "- `overnight_run.log` — training tail ending in the V8 ensemble summary at 68.42%.",
        "- `modernbert_large_v3_test_predictions.csv` — prediction output schema check only; header confirms `true_code`, `pred_code`, `confidence`.",
    ]

    model_list_lines = [
        f"- `{name}/` — {'artifact folder for the evolving Task 1/Task 2 system' if name in {'models', 'models_task2'} else 'experiment artifact folder in the model sweep; compare against the ensemble narrative in ENSEMBLE_DOCUMENTATION.md'}."
        for name in model_dirs
    ]

    todo_map: dict[str, list[str]] = defaultdict(list)

    nodes = [
        Node(
            "n1",
            "The Problem",
            "story",
            f"""
Morningstar's RED team owns a taxonomy that is both hierarchical and operationally important. Task 1 is the 145-class industry problem, while Task 2 pushes one level deeper into hundreds of business-activity labels. Our capstone question is simple to say and hard to solve: can NLP read long-form company text and route a firm into the right GECS code quickly enough to help analysts?

> "Morningstar's RED team owns the Global Equity Classification Standard (GECS) — a 4-level hierarchy that maps every public company to a sector → industry group → industry → business activity."

> "The case success criteria (stated): Macro F1 ≥ 0.75 overall"

The data gives us company descriptions, segment descriptions, revenue context, and the official Morningstar taxonomy definitions. The product ambition is not just a notebook score. It is an analyst-facing system that predicts a Task 1 industry, constrains Task 2 choices under that parent, returns alternatives, and leaves a review trail. The presentation needs to open there: the business pain is slow, manual, and consistency-sensitive classification across **{taxonomy_count}** GECS industry codes.

→ Next: Why It's Hard
""",
            ["HANDOFF_PLAYBOOK.md", "README.md", "gecs_taxonomy.json"],
            spine_step=1,
            next_node_id="n2",
            story_arc=True,
        ),
        Node(
            "n2",
            "Why It's Hard",
            "story",
            f"""
The difficulty is not just class count. The dataset itself bakes in ambiguity. We computed directly from `data/cleaned/task1_clean.csv` that **{multi_company_count}/{company_count} companies = 35.1%** are multi-code conglomerates, and those companies account for **{multi_rows}/{task1_rows} rows = 55.2%** of the training rows. The same `LongProfile` can appear with different segment labels, which means the model is asked to learn conflicting supervision from repeated text.

> "35.1% of companies in the dataset are diversified (multiple GECS codes across segments)."

> "This explains the universal ~68% plateau across every architecture we tried ... It wasn't an encoder problem. It was a data-preparation problem."

That ambiguity concentrates in class `31030010`, the diversified conglomerate bucket. The error is not accidental; it is where mixed businesses go when no single segment cleanly dominates. Any honest story about the model wall has to start here rather than with optimizer tricks.

→ Next: The Goal
""",
            ["CASCADE_AUDIT.md", "WEEK_5_PLAN.md", "data/cleaned/task1_clean.csv"],
            spine_step=2,
            next_node_id="n3",
            story_arc=True,
        ),
        Node(
            "n3",
            "The Goal",
            "story",
            f"""
The Monday target is **80%+ Macro F1** on `task1_test.csv`, the official 10,717-row holdout for Task 1. The choice of metric matters. Accuracy can look fine while rare classes fail completely; Macro F1 punishes that. In this problem, that is the right pressure, because Morningstar cares about the long tail and not just the obvious banks and software names.

> "Train/test split provided: `llm_finetuning/data/task1_train.csv` (42,868) and `task1_test.csv` (10,717)"

> "Macro F1 mathematically averages the score of all 145 classes equally."

The class count in the docs sometimes says 145 industries and sometimes 428 or 450 business-activity labels for Task 2, depending on whether filtered or raw labels are being discussed. For the briefing, Task 1 stays the headline metric: 145 classes, one honest holdout, and a success threshold high enough that a shallow accuracy win does not count.

→ Next: What We Tried First
""",
            ["HANDOFF_PLAYBOOK.md", "LLM_EVALUATION_STRATEGY.md", "README.md"],
            spine_step=3,
            next_node_id="n4",
            story_arc=True,
        ),
        Node(
            "n4",
            "What We Tried First",
            "story",
            f"""
The first half of the project is a ladder of increasingly expensive models with diminishing returns. The honest TF-IDF baseline landed at 59.65%. Hybrid classical stacks then climbed into the high 60s, and ModernBERT experiments pushed the neural lane closer to the low 70s on dev. The important takeaway is not that nothing improved; it is that each jump got smaller while the underlying ambiguity stayed in place.

> "| V2 (proper) | TF-IDF cascade, honest split | 59.65% | True baseline |"

> "| V8 | Mega-ensemble (TF-IDF + MiniLM + BGE + numerical) | **68.42%** | Ensembling encoders + features beats any single piece |"

{chart_f1_progression()}

The chart marks the requested Monday story points: TF-IDF at 59.65, V8 at 68.42, ModernBERT-base v2 at 67.18 test, and a ModernBERT-large epoch-3 dev checkpoint at 70.29. **TODO: confirm the exact source artifact for the 70.29 checkpoint before citing it aloud.**

→ Next: The Headline That Wasn't Real
""",
            ["PROJECT_JOURNEY.md", "RESULTS.md", "modernbert_large_v3_test_predictions.csv"],
            spine_step=4,
            next_node_id="n5",
            story_arc=True,
            synthesis_flag="Uses the user-requested 70.29 ModernBERT-large checkpoint, but that exact value was not found in the listed source docs.",
            todos=["Confirm the source artifact for the 70.29 ModernBERT-large dev checkpoint before presentation."],
        ),
        Node(
            "n5",
            "The Headline That Wasn't Real",
            "story",
            f"""
This is the pivot point of the entire capstone. The famous 88.90% result was not fabricated, but it was not a valid holdout result either. It came from evaluating on rows that had effectively already been seen in training. Once we audited that pipeline, the team stopped treating the pretty number as progress and started treating it as a failure mode.

> "Test rows present in training: 10,412 / 10,717 = 97.2%"

> "The reported **88.90% Macro F1** was real on the test rows, but ~97% of those rows had already been seen during training."

{chart_leakage_donut()}

This node should sit visually at the center of the graph because it explains everything that follows: why old docs look overconfident, why later docs sound sober, and why the team's credibility actually improved after the audit. The project stopped being a model race and became a methodology story.

→ Next: What We Learned From The Failure
""",
            ["CASCADE_AUDIT.md", "README.md", "PROJECT_JOURNEY.md"],
            spine_step=5,
            next_node_id="n6",
            story_arc=True,
        ),
        Node(
            "n6",
            "What We Learned From The Failure",
            "story",
            """
After the leakage audit, the central lesson changed from "find a stronger encoder" to "fix the supervision problem." Every serious architecture started converging near the same ceiling because they were all reading the same contaminated row construction. That is why the Week 5 plan stops talking about more flat classifiers and starts talking about segment-only inputs, hierarchy-aware heads, and analyst review for conglomerates.

> "No more flat 145-class classifiers without hierarchy awareness."

> "This explains the universal ~68% plateau across every architecture we tried ... It wasn't an encoder problem. It was a data-preparation problem."

One way to say the same thing to the class is this: if single-code companies can be solved well but multi-code conglomerates remain structurally noisy, the global ceiling is set by data ambiguity before it is set by architecture. **That ceiling arithmetic is a synthesis, not a direct quote, so confirm the exact number before putting it on a slide.**

→ Next: The Honest Baseline Today
""",
            ["WEEK_5_PLAN.md", "CASCADE_AUDIT.md", "HANDOFF_PLAYBOOK.md"],
            spine_step=6,
            next_node_id="n7",
            story_arc=True,
            synthesis_flag="The ceiling explanation and any single-code vs multi-code arithmetic are synthesized from the audit and Week 5 plan rather than stated verbatim.",
        ),
        Node(
            "n7",
            "The Honest Baseline Today",
            "story",
            f"""
The repo now has the infrastructure for company-aware evaluation: `task1_train_with_companyid.csv` joined **{train_joined}/{train_total} = 98.2%**, and `task1_test_with_companyid.csv` joined **{test_joined}/{test_total} = 98.3%**. Those files matter because they make per-company reasoning, ambiguity analysis, and weighted evaluation possible. They are the opposite of leakage: extra bookkeeping to prove what each row really represents.

> "The actual current best deployable artifact is V13 (67.99%), NOT V10."

> "Best honest result so far: **V10 calibrated stack — 69.09% Macro F1**"

The Monday node the team probably wants is "ModernBERT-large 70.29% dev macro F1, 71.4% industry accuracy on real company-disjoint joins." That exact claim was **not** present in the listed source docs. **TODO: confirm the artifact path and metric file with the team before saying it defensibly.** Until that is confirmed, the documented honest floor is the V13/V10 range, with the new `_with_companyid.csv` files as the evidence that the evaluation story is finally clean.

→ Next: Four Paths to 80%+
""",
            ["HANDOFF_PLAYBOOK.md", "WEEK_5_PLAN.md", "llm_finetuning/data/task1_train_with_companyid.csv", "llm_finetuning/data/task1_test_with_companyid.csv"],
            spine_step=7,
            next_node_id="n8",
            story_arc=True,
            synthesis_flag="The requested 70.29 dev / 71.4 accuracy claim is not documented in the listed source files, so the node leaves it as a TODO rather than a settled fact.",
            todos=["Confirm whether the 2026-05-13 company-aware ModernBERT-large result is 70.29 dev Macro F1 / 71.4 accuracy, and cite the exact artifact if true."],
        ),
        Node(
            "n8",
            "Four Paths to 80%+",
            "story",
            """
A useful Monday framing is that not every route to 80 behaves the same way. Some are metric reframings, some are cleaner product metrics, and one looks like the strongest honest modeling path. The sources support the hierarchy-aware direction most strongly; the rest should be pitched as options, not completed wins.

> "Use SegmentName + SegmentDescription only (no LongProfile — that was the contamination source)"

> "Realistic landing zone after Week 5 work: **74–77% Macro F1**"

Path A: decidable-subset Macro F1 for single-code or low-ambiguity companies. Path B: revenue-share-weighted per-company scoring once `CompanyId` joins are complete. Path C: sector-conditioned or multi-head ModernBERT on cleaned segment inputs; this is the strongest legitimate route. Path D: brute-force longer training on the same contaminated rows, which the docs suggest will stall. **TODO: confirm which of these four paths the team wants to present as the primary Monday recommendation.**

→ Next: Where We Are Right Now (2026-05-14)
""",
            ["HANDOFF_PLAYBOOK.md", "WEEK_5_PLAN.md", "PROJECT_JOURNEY.md"],
            spine_step=8,
            next_node_id="n9",
            story_arc=True,
            synthesis_flag="The four-path packaging is synthesized from planning notes, artifact joins, and model-history documents rather than listed as one canonical source table.",
            todos=["Confirm whether Monday should emphasize Path C only, or show all four 80% paths as alternatives."],
        ),
        Node(
            "n9",
            "Where We Are Right Now (2026-05-14)",
            "story",
            """
This node is intentionally conservative and uses only `WEEK_5_PLAN.md`, `LEGENDARY_ROADMAP.md`, and `HANDOFF_PLAYBOOK.md`. Those documents do not fully agree with each other, so the safest story is a status board with visible open items instead of a fake single truth.

> "**Status:** COMPLETE ✅"

> "| Working live Hugging Face Space URL | ⏳ Deploy Wed | Akash + Codex |"

- Done in docs: the roadmap claims the legendary stack is complete, and the handoff says the core decisions are locked.
- Waiting in docs: HF Space deploy, final report, slide polish, Task 2 constrained build, and the insurance V10 artifact were still pending in the handoff checklist.
- TODO: confirm with team which status doc is canonical for Monday.
- TODO: confirm whether the frontend wiring is demo-ready or still a partial shell.
- TODO: confirm whether the company-aware ModernBERT lane has become the new official headline.

→ Next: Monday Presentation Plan
""",
            ["WEEK_5_PLAN.md", "LEGENDARY_ROADMAP.md", "HANDOFF_PLAYBOOK.md"],
            spine_step=9,
            next_node_id="n10",
            story_arc=True,
            todos=[
                "Confirm which status document is canonical: LEGENDARY_ROADMAP says complete, HANDOFF_PLAYBOOK still shows multiple Wednesday/Thursday deliverables pending.",
                "Confirm frontend demo readiness.",
                "Confirm whether the company-aware ModernBERT lane is now the official headline.",
            ],
        ),
        Node(
            "n10",
            "Monday Presentation Plan",
            "story",
            """
This last spine node is mostly scaffolding by design. The source docs give a pitch arc and a closing line, but they do not lock speaker order, final demo owner, or the exact Q&A split. That means the page should help the team rehearse without pretending those assignments already exist.

> "Act I (Weeks 1–3): 'We built a TF-IDF cascade and got 88.90% Macro F1. We almost shipped it.'"

> "Act II (Week 4): 'We audited our own evaluation pipeline. 97.2% of our test set was in training.'"

### Claim
TODO: lock the one-sentence claim the team will stand behind on Monday.

### Demo
TODO: choose whether the projector demo is HF Space first, localhost first, or both.

### Speaking parts
TODO: assign opening, audit story, model story, product story, and Q&A closer.

### FAQ
TODO: pre-answer the leakage question, the 80% gap question, and the "why not GPT-4?" question.

→ Next: End of story
""",
            ["HANDOFF_PLAYBOOK.md"],
            spine_step=10,
            next_node_id=None,
            story_arc=True,
            todos=[
                "Lock the one-sentence presentation claim.",
                "Choose the live demo order.",
                "Assign speaking parts.",
                "Finalize FAQ ownership.",
            ],
        ),
        Node(
            "d1",
            "The Data",
            "data",
            f"""
`data/cleaned/task1_clean.csv` is the backbone dataset for Task 1. We counted **{task1_rows:,} rows × {len(task1_cols)} columns** and confirmed the header includes `CompanyId`, `LongProfile`, `SegmentName`, `SegmentDescription`, `Revenue`, `total_revenue_company_as_of`, `revenue_share`, `is_largest_share_segment`, and `MstarGlobal`. The one extra column is `AsOfDate`, which matters for joins and per-company tracking. The presence of revenue-share features is what makes company-weighted scoring and conglomerate analysis possible later.
""",
            ["data/cleaned/task1_clean.csv"],
        ),
        Node(
            "d2",
            "Critical Artifacts (2026-05-13)",
            "data",
            "The new `_with_companyid.csv` files are the bridge between row-level benchmarks and company-aware analysis. We verified `task1_train_with_companyid.csv` joins `42,116/42,868 = 98.2%` rows and `task1_test_with_companyid.csv` joins `10,535/10,717 = 98.3%`. The join logic in `scripts/enrich_test_with_metadata.py` builds a unique `LongProfile` prefix map, first at 200 characters and then with a shorter fallback. Without these joins, company-level options like ambiguity audits and revenue-weighted evaluation remain theory.",
            ["llm_finetuning/data/task1_train_with_companyid.csv", "llm_finetuning/data/task1_test_with_companyid.csv", "scripts/enrich_test_with_metadata.py"],
        ),
        Node(
            "m1",
            "Models We Trained",
            "models",
            "The repo tells the story of a broad model sweep rather than a single silver bullet. The core pattern in `ENSEMBLE_DOCUMENTATION.md` is clear: one model family handles head classes, another helps on semantic similarity, and the ensemble exists because the 145-class long tail punishes any single view of the text.\n\n" + "\n".join(model_list_lines),
            ["ENSEMBLE_DOCUMENTATION.md"],
        ),
        Node(
            "m2",
            "Serving Stack",
            "models",
            """
The local serving stack is split by responsibility. `server.py` is the production cascade on port 5000. `server_llm.py` is the DeBERTa microservice on 5001. `server_cascade.py` is the cascade-only path on 5002. `server_legendary.py` is the extended local stack on 5003. The final report explicitly notes that `server_legendary.py` runs via Waitress on Windows because the Flask development server is unstable there under Python 3.11.
""",
            ["CAPSTONE_FINAL_REPORT.md", "README.md"],
        ),
        Node(
            "m3",
            "Frontend",
            "team",
            """
The frontend lives in `frontend/` and the source docs describe it as a Next.js app that proxies predictions to the local API. The current readable status is mixed: the README says the proxy defaults to `http://localhost:5003`, while the handoff frames the frontend as an existing UI that still needs final pages and polish. The app folder itself already includes routes like `demo`, `dashboard`, `features`, `journey`, and `team`, which suggests a strong shell even if Monday readiness still needs confirmation.
""",
            ["README.md", "HANDOFF_PLAYBOOK.md", "CODEX_BUILD_TASKS.md", "frontend/app"],
        ),
        Node(
            "m4",
            "Hugging Face Space",
            "plan",
            """
`hf_space/` exists in the repo with an `app.py`, `README.md`, and requirements file, which matches the product direction in the handoff and revamp docs. The Monday plan treats the Space as the public demo URL and the laptop demo as the backup. The handoff is explicit that both need to be tested on Monday morning. The docs also warn not to depend on Ollama there; local reasoning can exist, but the free-tier Space must stay lightweight and reliable.
""",
            ["HANDOFF_PLAYBOOK.md", "FULL_SYSTEM_REVAMP.md", "hf_space/app.py"],
        ),
        Node(
            "t1",
            "Team Roles & Speaking Parts",
            "team",
            """
The readable sources give us a roster but not a final speaking order. `Capstone Week 2 Team Doc.docx` lists Akash, Tserennad, Srilaxmi, Vishal, and Subasree. `Week3_Team_Classifier_Assignments.docx` assigns Week 3 classifier work by member number and model family, but it does not map those roles to Monday presentation segments. TODO: assign who covers the audit, who covers the model journey, who drives the demo, and who closes Q&A.
""",
            ["Capstone Week 2 Team Doc.docx", "Week3_Team_Classifier_Assignments.docx"],
            todos=["Assign speaking parts to named teammates."],
        ),
        Node(
            "t2",
            "5-Minute Demo Script",
            "team",
            """
The sourceable launch path is straightforward even though `Launch notes.txt` is empty. Start the extended local stack with `python server_legendary.py`. If you need the simpler production path, `python server.py` launches the main cascade server on port 5000. For the live walk-through, the cleanest narrative is: paste a company description, show Task 1, show the constrained Task 2 output, open the top-3 alternatives, and point to the review controls. TODO: lock the exact sample query and whether the team will demo HF Space first or localhost first.
""",
            ["HANDOFF_PLAYBOOK.md", "CAPSTONE_FINAL_REPORT.md", "Launch notes.txt"],
            todos=["Choose the exact demo query.", "Choose whether HF Space or localhost is the first demo surface."],
        ),
        Node(
            "t3",
            "Hard Questions FAQ",
            "team",
            """
TODO: finalize answer wording with the team. The obvious questions are already visible from the docs: Why was 88.90% invalid? Why is 80% still hard if we tried so many models? Why ModernBERT over DeBERTa? Why not GPT-4 or another API model? The best answers all return to the same themes: the audit, the taxonomy grounding, the long tail, the conglomerate ambiguity, and the analyst-in-the-loop product stance.
""",
            ["CASCADE_AUDIT.md", "HANDOFF_PLAYBOOK.md", "LLM_EVALUATION_STRATEGY.md"],
            todos=[
                "Finalize leakage answer wording.",
                "Finalize 80% gap answer wording.",
                "Finalize ModernBERT-vs-DeBERTa answer wording.",
                "Finalize why-not-GPT answer wording.",
            ],
        ),
        Node(
            "t4",
            "Open Risks",
            "plan",
            """
TODO scaffold only, because the docs still show multiple moving parts. Confirm whether the Option C or hierarchy-aware ModernBERT training lane has landed. Confirm whether the frontend is fully wired for the Monday demo. Confirm whether the slide deck is complete. Confirm who is presenting each segment. The handoff also keeps calling out two operational risks: the live Hugging Face Space URL may fail, and the team should not walk into class without a tested laptop fallback.
""",
            ["HANDOFF_PLAYBOOK.md", "FULL_SYSTEM_REVAMP.md", "WEEK_5_PLAN.md"],
            todos=[
                "Confirm Option C / hierarchy-aware training status.",
                "Confirm frontend wiring status.",
                "Confirm deck completion status.",
                "Confirm presenter ownership.",
            ],
        ),
        Node(
            "r1",
            "File Map",
            "reference",
            "Here is the root-level document map used for this briefing:\n\n" + "\n".join(file_map_lines),
            SOURCE_FILES,
        ),
    ]

    for node in nodes:
        if node.todos:
            todo_map[node.title].extend(node.todos)
    return nodes, todo_map


def build_links(nodes: list[Node]) -> list[dict[str, str | int]]:
    links: list[dict[str, str | int]] = []
    for left, right in zip([n for n in nodes if n.story_arc][:-1], [n for n in nodes if n.story_arc][1:]):
        links.append({"source": left.node_id, "target": right.node_id, "story": 1})
    support_map = {
        "d1": "n1",
        "d2": "n2",
        "m1": "n4",
        "m2": "n7",
        "m3": "n9",
        "m4": "n10",
        "t1": "n10",
        "t2": "n10",
        "t3": "n10",
        "t4": "n9",
        "r1": "n5",
    }
    for source, target in support_map.items():
        links.append({"source": source, "target": target, "story": 0})
    return links


def positions_for(nodes: list[Node]) -> dict[str, tuple[int, int]]:
    spine_positions = {
        "n1": (180, 240),
        "n2": (360, 170),
        "n3": (560, 130),
        "n4": (760, 170),
        "n5": (880, 320),
        "n6": (1120, 190),
        "n7": (1320, 150),
        "n8": (1500, 210),
        "n9": (1410, 430),
        "n10": (1180, 560),
        "d1": (160, 440),
        "d2": (390, 420),
        "m1": (720, 390),
        "m2": (1080, 380),
        "m3": (1540, 430),
        "m4": (1510, 590),
        "t1": (1000, 690),
        "t2": (1220, 760),
        "t3": (1410, 760),
        "t4": (1600, 620),
        "r1": (670, 570),
    }
    return spine_positions


def render_html(nodes: list[Node], unreadable: list[tuple[str, str]], todo_map: dict[str, list[str]]) -> str:
    md = mistune.create_markdown(escape=False)
    d3_bundle = read_text(ROOT / "frontend/node_modules/d3/dist/d3.min.js")
    positions = positions_for(nodes)
    node_payload = []
    for node in nodes:
        body_html = panel_html(md, node.body_markdown, node.sources)
        x, y = positions[node.node_id]
        node_payload.append(
            {
                "id": node.node_id,
                "title": node.title,
                "category": node.category,
                "categoryLabel": CATEGORY_LABELS.get(node.category, node.category.title()),
                "spineStep": node.spine_step,
                "nextNodeId": node.next_node_id,
                "storyArc": node.story_arc,
                "content": body_html,
                "tx": x,
                "ty": y,
                "radius": 44 if node.node_id == "n5" else (28 if node.story_arc else 10),
            }
        )
    payload = {
        "nodes": node_payload,
        "links": build_links(nodes),
    }
    unreadable_note = ""
    if unreadable:
        items = "".join(f"<li>{escape(name)} — {escape(reason)}</li>" for name, reason in unreadable)
        unreadable_note = f'<div class="build-note"><strong>Unreadable during build:</strong><ul>{items}</ul></div>'

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>MGT 599 Group 4 · Capstone Briefing</title>
  <style>
    :root {{
      --bg: #14161f;
      --canvas: #171923;
      --canvas-deep: #11131b;
      --panel: #1d202b;
      --panel-soft: #242836;
      --panel-border: rgba(148, 163, 184, 0.16);
      --text: #e7ecf5;
      --muted: #98a2b3;
      --muted-2: #6b7486;
      --story: #5eead4;
      --data: #6ee7b7;
      --models: #c084fc;
      --results: #f6c453;
      --problems: #fb7185;
      --plan: #fb923c;
      --team: #b6c2d2;
      --reference: #7b8798;
      --shadow: 0 18px 60px rgba(0, 0, 0, 0.42);
    }}
    * {{ box-sizing: border-box; }}
    html, body {{ margin: 0; height: 100%; background: var(--bg); color: var(--text); font-family: "Segoe UI", Arial, sans-serif; }}
    body {{ overflow: hidden; }}
    a {{ color: #8bd5ff; }}
    #app {{ position: relative; width: 100vw; height: 100vh; }}
    .topbar {{
      position: absolute; top: 0; left: 0; right: 0; height: 58px;
      display: flex; align-items: center; justify-content: flex-start;
      padding: 0 22px;
      background: linear-gradient(180deg, rgba(10, 12, 18, 0.96), rgba(20, 22, 31, 0.9));
      backdrop-filter: blur(10px);
      border-bottom: 1px solid rgba(148, 163, 184, 0.1);
      z-index: 20; font-weight: 650; letter-spacing: 0.02em;
      color: #dce4ef;
    }}
    .graph-wrap {{
      position: absolute; inset: 58px 0 0 0; overflow: hidden;
      background:
        radial-gradient(circle at 18% 18%, rgba(36, 52, 86, 0.28), transparent 0 26%),
        radial-gradient(circle at 82% 24%, rgba(14, 116, 144, 0.18), transparent 0 22%),
        radial-gradient(circle at 72% 74%, rgba(84, 56, 144, 0.18), transparent 0 24%),
        linear-gradient(180deg, var(--canvas), var(--canvas-deep));
    }}
    .graph-wrap::before {{
      content: "";
      position: absolute; inset: 0;
      background-image:
        radial-gradient(rgba(128, 142, 170, 0.12) 0.8px, transparent 0.8px),
        linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px);
      background-size: 24px 24px, 96px 96px, 96px 96px;
      opacity: 0.55;
      pointer-events: none;
    }}
    .graph-wrap::after {{
      content: "";
      position: absolute; inset: 0;
      background: radial-gradient(circle at center, transparent 42%, rgba(8, 10, 15, 0.12) 68%, rgba(8, 10, 15, 0.46) 100%);
      pointer-events: none;
    }}
    #graph {{ width: 100%; height: 100%; display: block; position: relative; z-index: 1; }}
    .legend {{
      position: absolute; left: 22px; bottom: 24px; z-index: 12;
      background: rgba(23, 25, 35, 0.86); border: 1px solid var(--panel-border);
      border-radius: 18px; padding: 13px 14px; width: 208px;
      box-shadow: var(--shadow);
      backdrop-filter: blur(8px);
    }}
    .legend h3 {{ margin: 0 0 10px 0; font-size: 13px; text-transform: uppercase; letter-spacing: 0.12em; color: #c8d2df; }}
    .legend-row {{ display: flex; align-items: center; gap: 10px; margin: 7px 0; font-size: 12px; color: var(--muted); }}
    .swatch {{ width: 10px; height: 10px; border-radius: 999px; box-shadow: 0 0 0 5px rgba(255,255,255,0.04); }}
    .story-btn {{
      position: absolute; left: 50%; bottom: 20px; transform: translateX(-50%);
      z-index: 12; border: 1px solid rgba(94, 234, 212, 0.25);
      background: linear-gradient(180deg, rgba(45, 61, 83, 0.9), rgba(29, 33, 46, 0.94));
      color: #effcfb; padding: 12px 18px; border-radius: 999px; cursor: pointer;
      font-size: 13px; font-weight: 700; box-shadow: var(--shadow); letter-spacing: 0.02em;
    }}
    .panel {{
      position: absolute; top: 68px; right: 18px; width: min(48vw, 840px); min-width: 440px;
      height: calc(100vh - 88px); background: linear-gradient(180deg, rgba(31, 35, 48, 0.98), rgba(25, 28, 38, 0.98));
      border: 1px solid var(--panel-border); border-radius: 22px; transform: translateX(calc(100% + 26px));
      transition: transform 260ms ease; z-index: 18; display: flex; flex-direction: column;
      box-shadow: var(--shadow); overflow: hidden;
    }}
    .panel.open {{ transform: translateX(0); }}
    .panel-head {{
      display: flex; align-items: center; justify-content: space-between; gap: 16px;
      padding: 18px 22px 14px; border-bottom: 1px solid rgba(148,163,184,0.12);
      background: linear-gradient(180deg, rgba(40, 45, 60, 0.88), rgba(29, 33, 45, 0.74));
    }}
    .panel-title-wrap h2 {{ margin: 8px 0 0 0; font-size: 28px; line-height: 1.12; }}
    .panel-meta {{ display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }}
    .step-indicator {{ color: var(--muted); font-size: 11px; text-transform: uppercase; letter-spacing: 0.14em; }}
    .category-badge {{
      display: inline-flex; align-items: center; gap: 8px; padding: 5px 10px;
      border-radius: 999px; border: 1px solid rgba(148,163,184,0.14);
      font-size: 11px; letter-spacing: 0.08em; text-transform: uppercase;
      color: #d8e1ec; background: rgba(255,255,255,0.03);
    }}
    .close-btn {{
      border: 1px solid rgba(148,163,184,0.18); background: rgba(255,255,255,0.03); color: var(--text);
      border-radius: 999px; width: 38px; height: 38px; cursor: pointer; font-size: 18px;
    }}
    .panel-body {{
      padding: 26px 28px 34px; overflow: auto; line-height: 1.68;
      background: linear-gradient(180deg, rgba(255,255,255,0.02), transparent 18%), linear-gradient(180deg, rgba(17, 20, 28, 0.08), rgba(17, 20, 28, 0.16));
    }}
    .panel-body p:first-child {{ margin-top: 0; }}
    .panel-body blockquote {{
      margin: 16px 0; padding: 14px 16px; border-left: 3px solid #7dd3fc;
      color: #dbeafe; background: rgba(63, 76, 99, 0.24); border-radius: 0 14px 14px 0;
    }}
    .panel-body h3 {{ margin-top: 28px; margin-bottom: 10px; font-size: 15px; text-transform: uppercase; letter-spacing: 0.14em; color: #c7d2df; }}
    .panel-body ul, .panel-body ol {{ padding-left: 22px; }}
    .panel-body li {{ margin: 7px 0; }}
    .panel-body code {{ background: rgba(255,255,255,0.05); border: 1px solid rgba(148,163,184,0.1); padding: 2px 6px; border-radius: 8px; font-size: 0.95em; }}
    .inline-chart {{ width: 100%; margin: 18px 0 6px; display: block; }}
    .donut-chart {{ max-width: 420px; margin-left: auto; margin-right: auto; }}
    .sources {{
      margin-top: 24px; padding-top: 16px; border-top: 1px solid rgba(148,163,184,0.14);
      color: var(--muted); font-size: 13px;
    }}
    .sources a {{
      display: inline-flex; align-items: center; margin: 6px 8px 0 0; padding: 6px 10px;
      border-radius: 999px; text-decoration: none; background: rgba(255,255,255,0.04);
      border: 1px solid rgba(148,163,184,0.12);
    }}
    .panel-nav {{
      display: flex; align-items: center; justify-content: space-between; gap: 12px;
      padding: 14px 22px 18px; border-top: 1px solid rgba(148,163,184,0.12); background: rgba(20, 23, 31, 0.68);
    }}
    .panel-nav .hint {{ color: var(--muted); font-size: 12px; }}
    .next-btn {{
      border: 1px solid rgba(94, 234, 212, 0.22);
      background: linear-gradient(180deg, rgba(62, 83, 110, 0.88), rgba(33, 39, 53, 0.95));
      color: #f0fffd; padding: 10px 14px; border-radius: 999px; cursor: pointer; font-weight: 700;
    }}
    .build-note {{
      position: absolute; top: 72px; left: 22px; z-index: 13; max-width: 360px;
      background: rgba(87, 25, 37, 0.9); border: 1px solid rgba(248,113,113,0.28);
      border-radius: 16px; padding: 12px 14px; color: #fee2e2; font-size: 12px; box-shadow: var(--shadow);
    }}
    .node-label {{
      pointer-events: none; fill: #dbe4ef; font-size: 11px; font-weight: 600; text-anchor: middle;
      opacity: 0; transition: opacity 120ms ease;
    }}
    .node-label.story {{ font-size: 12px; opacity: 1; fill: #f4f8fe; }}
    .node-label.visible, .node-label.active-label {{ opacity: 1; }}
    .help-chip {{
      position: absolute; right: 18px; bottom: 20px; z-index: 12;
      background: rgba(23, 25, 35, 0.82); border: 1px solid var(--panel-border);
      border-radius: 999px; padding: 10px 12px; color: var(--muted); font-size: 12px; box-shadow: var(--shadow); backdrop-filter: blur(8px);
    }}
    .graph-node.dimmed {{ opacity: 0.16; }}
    .graph-node.selected, .graph-node.neighbor {{ opacity: 1; }}
    .graph-link.dimmed {{ opacity: 0.08; }}
    .graph-link.active-link {{ opacity: 1; }}
    .node-halo {{ opacity: 0.18; filter: url(#nodeGlow); }}
    .node-core {{ stroke-width: 1.8; transition: transform 140ms ease, opacity 140ms ease, stroke-width 140ms ease; }}
    .story-shell {{ fill: rgba(255,255,255,0.01); stroke: rgba(226, 232, 240, 0.18); stroke-width: 1.2; stroke-dasharray: 3 5; }}
    .graph-node.support-node .node-core {{ opacity: 0.92; }}
    .graph-node.story-node .node-core {{ stroke: rgba(255,255,255,0.58); }}
    .graph-node.selected .node-core {{ stroke-width: 2.8; opacity: 1; }}
    .graph-node.selected .node-halo, .graph-node.neighbor .node-halo {{ opacity: 0.34; }}
    .graph-node.selected .story-shell {{ stroke: rgba(255,255,255,0.4); }}
    .graph-node.selected .node-label, .graph-node.neighbor .node-label {{ opacity: 1; }}
  </style>
</head>
<body>
  <div id="app">
    <div class="topbar">MGT 599 Group 4 · Capstone Briefing for Monday 2026-05-18 · Built 2026-05-14</div>
    <div class="graph-wrap"><svg id="graph"></svg></div>
    <div class="legend">
      <h3>Legend</h3>
      <div class="legend-row"><span class="swatch" style="background: var(--story)"></span>Story</div>
      <div class="legend-row"><span class="swatch" style="background: var(--data)"></span>Data</div>
      <div class="legend-row"><span class="swatch" style="background: var(--models)"></span>Models</div>
      <div class="legend-row"><span class="swatch" style="background: var(--results)"></span>Results</div>
      <div class="legend-row"><span class="swatch" style="background: var(--problems)"></span>Problems / Audit</div>
      <div class="legend-row"><span class="swatch" style="background: var(--plan)"></span>Plan</div>
      <div class="legend-row"><span class="swatch" style="background: var(--team)"></span>Team / Logistics</div>
      <div class="legend-row"><span class="swatch" style="background: var(--reference)"></span>Reference</div>
    </div>
    <button id="storyBtn" class="story-btn">▶ Start the Story</button>
    <div class="help-chip">Click a node · Esc closes · ← → moves along the story</div>
    {unreadable_note}
    <aside id="panel" class="panel" aria-hidden="true">
      <div class="panel-head">
        <div class="panel-title-wrap">
          <div class="panel-meta">
            <div id="stepIndicator" class="step-indicator"></div>
            <div id="categoryBadge" class="category-badge"></div>
          </div>
          <h2 id="panelTitle"></h2>
        </div>
        <button id="closePanel" class="close-btn" aria-label="Close panel">×</button>
      </div>
      <div id="panelBody" class="panel-body"></div>
      <div class="panel-nav">
        <div class="hint">Story nodes support keyboard navigation.</div>
        <button id="nextBtn" class="next-btn">→ Next</button>
      </div>
    </aside>
  </div>

  <script>{d3_bundle}</script>
  <script>
    const graphData = {json.dumps(payload)};
    const categoryColor = {{
      story: getComputedStyle(document.documentElement).getPropertyValue('--story').trim(),
      data: getComputedStyle(document.documentElement).getPropertyValue('--data').trim(),
      models: getComputedStyle(document.documentElement).getPropertyValue('--models').trim(),
      results: getComputedStyle(document.documentElement).getPropertyValue('--results').trim(),
      problems: getComputedStyle(document.documentElement).getPropertyValue('--problems').trim(),
      plan: getComputedStyle(document.documentElement).getPropertyValue('--plan').trim(),
      team: getComputedStyle(document.documentElement).getPropertyValue('--team').trim(),
      reference: getComputedStyle(document.documentElement).getPropertyValue('--reference').trim(),
    }};
    const svg = d3.select('#graph');
    const panel = document.getElementById('panel');
    const panelTitle = document.getElementById('panelTitle');
    const panelBody = document.getElementById('panelBody');
    const stepIndicator = document.getElementById('stepIndicator');
    const categoryBadge = document.getElementById('categoryBadge');
    const nextBtn = document.getElementById('nextBtn');
    const storyBtn = document.getElementById('storyBtn');
    const closePanelBtn = document.getElementById('closePanel');
    const storyNodes = graphData.nodes.filter(d => d.spineStep).sort((a, b) => a.spineStep - b.spineStep);
    const nodeById = new Map(graphData.nodes.map(d => [d.id, d]));
    let storyMode = false;
    let currentNode = null;
    let selectedId = null;

    function sizeGraph() {{
      const rect = document.querySelector('.graph-wrap').getBoundingClientRect();
      svg.attr('viewBox', `0 0 ${{rect.width}} ${{rect.height}}`);
      return rect;
    }}

    let rect = sizeGraph();
    const defs = svg.append('defs');
    const glow = defs.append('filter').attr('id', 'nodeGlow');
    glow.append('feGaussianBlur').attr('stdDeviation', 5).attr('result', 'coloredBlur');
    const merge = glow.append('feMerge');
    merge.append('feMergeNode').attr('in', 'coloredBlur');
    merge.append('feMergeNode').attr('in', 'SourceGraphic');

    const canvas = svg.append('g');
    const linkLayer = canvas.append('g');
    const nodeLayer = canvas.append('g');
    const labelLayer = canvas.append('g');

    const links = graphData.links.map(d => Object.assign({{}}, d));
    const nodes = graphData.nodes.map(d => Object.assign({{}}, d));
    const neighborMap = new Map(nodes.map(n => [n.id, new Set([n.id])]));
    links.forEach(l => {{
      neighborMap.get(l.source)?.add(l.target);
      neighborMap.get(l.target)?.add(l.source);
    }});

    const simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(links).id(d => d.id).distance(l => l.story ? 168 : 142).strength(l => l.story ? 0.92 : 0.44))
      .force('charge', d3.forceManyBody().strength(d => d.storyArc ? -430 : -135))
      .force('collision', d3.forceCollide().radius(d => d.storyArc ? d.radius + 34 : d.radius + 16))
      .force('x', d3.forceX(d => d.tx).strength(d => d.storyArc ? 0.28 : 0.17))
      .force('y', d3.forceY(d => d.ty).strength(d => d.storyArc ? 0.28 : 0.17))
      .alpha(1)
      .alphaDecay(0.032)
      .velocityDecay(0.34);

    const link = linkLayer.selectAll('line')
      .data(links)
      .join('line')
      .attr('class', 'graph-link')
      .attr('stroke', d => d.story ? 'rgba(94,234,212,0.68)' : 'rgba(148,163,184,0.16)')
      .attr('stroke-width', d => d.story ? 5.6 : 1.3)
      .attr('stroke-linecap', 'round')
      .attr('stroke-linejoin', 'round');

    const node = nodeLayer.selectAll('g')
      .data(nodes)
      .join('g')
      .attr('class', d => `graph-node ${{d.storyArc ? 'story-node' : 'support-node'}} ${{d.id === 'n5' ? 'leak-node' : ''}}`)
      .style('cursor', 'pointer')
      .on('click', (_, d) => openNode(d, false))
      .on('mouseenter', (_, d) => highlightNeighbors(d))
      .on('mouseleave', clearHighlight);

    node.append('circle')
      .attr('class', 'node-halo')
      .attr('r', d => d.storyArc ? d.radius + 10 : d.radius + 5)
      .attr('fill', d => d.id === 'n5' ? categoryColor.problems : (categoryColor[d.category] || '#94a3b8'));

    node.filter(d => d.storyArc).append('circle')
      .attr('class', 'story-shell')
      .attr('r', d => d.radius + 2);

    node.append('circle')
      .attr('class', 'node-core')
      .attr('r', d => d.radius)
      .attr('fill', d => d.id === 'n5' ? categoryColor.problems : (categoryColor[d.category] || '#94a3b8'))
      .attr('stroke', d => d.id === 'n5' ? '#fecdd3' : 'rgba(255,255,255,0.36)');

    const label = labelLayer.selectAll('text')
      .data(nodes)
      .join('text')
      .attr('class', d => `node-label ${{d.storyArc ? 'story visible' : ''}}`);

    label.each(function(d) {{
      const maxChars = d.storyArc ? 16 : 18;
      const words = d.title.split(/\\s+/);
      const lines = [];
      let current = '';
      words.forEach(word => {{
        if ((current + ' ' + word).trim().length <= maxChars) {{
          current = (current + ' ' + word).trim();
        }} else {{
          if (current) lines.push(current);
          current = word;
        }}
      }});
      if (current) lines.push(current);
      const el = d3.select(this);
      lines.slice(0, 4).forEach((lineText, idx) => {{
        el.append('tspan')
          .attr('x', 0)
          .attr('dy', idx === 0 ? (d.storyArc ? d.radius + 20 : d.radius + 16) : 12)
          .text(lineText);
      }});
    }});

    simulation.on('tick', () => {{
      link
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y);
      node.attr('transform', d => `translate(${{d.x}}, ${{d.y}})`);
      label.attr('transform', d => `translate(${{d.x}}, ${{d.y}})`);
    }});

    function connectedIds(nodeDatum) {{
      const connected = new Set([nodeDatum.id]);
      links.forEach(l => {{
        const s = typeof l.source === 'object' ? l.source.id : l.source;
        const t = typeof l.target === 'object' ? l.target.id : l.target;
        if (s === nodeDatum.id || t === nodeDatum.id) {{
          connected.add(s);
          connected.add(t);
        }}
      }});
      return connected;
    }}

    function updateSelectionStyles(focusIds = null) {{
      const active = focusIds || (selectedId ? connectedIds(nodeById.get(selectedId)) : null);
      node
        .classed('selected', d => d.id === selectedId)
        .classed('neighbor', d => active ? active.has(d.id) && d.id !== selectedId : false)
        .classed('dimmed', d => active ? !active.has(d.id) : false);
      label
        .classed('active-label', d => active ? active.has(d.id) : false)
        .classed('visible', d => d.storyArc || (active ? active.has(d.id) : false))
        .style('opacity', d => (d.storyArc || (active ? active.has(d.id) : false)) ? 1 : 0);
      link
        .classed('active-link', d => {{
          const s = typeof d.source === 'object' ? d.source.id : d.source;
          const t = typeof d.target === 'object' ? d.target.id : d.target;
          return active ? active.has(s) && active.has(t) : false;
        }})
        .classed('dimmed', d => {{
          const s = typeof d.source === 'object' ? d.source.id : d.source;
          const t = typeof d.target === 'object' ? d.target.id : d.target;
          return active ? !(active.has(s) && active.has(t)) : false;
        }});
    }}

    function highlightNeighbors(nodeDatum) {{
      updateSelectionStyles(connectedIds(nodeDatum));
    }}

    function clearHighlight() {{
      updateSelectionStyles();
    }}

    function openNode(nodeDatum, fromStory) {{
      currentNode = nodeDatum;
      selectedId = nodeDatum.id;
      if (fromStory) storyMode = true;
      panelTitle.textContent = nodeDatum.title;
      panelBody.innerHTML = nodeDatum.content;
      categoryBadge.textContent = nodeDatum.categoryLabel;
      categoryBadge.style.boxShadow = `inset 0 0 0 1px ${{(categoryColor[nodeDatum.category] || '#94a3b8')}}33`;
      categoryBadge.style.color = categoryColor[nodeDatum.category] || '#d8e1ec';
      if (nodeDatum.spineStep) {{
        stepIndicator.textContent = `Step ${{nodeDatum.spineStep}} / 10`;
        nextBtn.style.visibility = nodeDatum.nextNodeId ? 'visible' : 'hidden';
      }} else {{
        stepIndicator.textContent = storyMode ? 'Supporting node' : 'Explore mode';
        nextBtn.style.visibility = 'hidden';
      }}
      panel.classList.add('open');
      panel.setAttribute('aria-hidden', 'false');
      updateSelectionStyles();
      focusNode(nodeDatum);
    }}

    function focusNode(nodeDatum) {{
      simulation.alphaTarget(0.04).restart();
      const dx = rect.width / 2 - nodeDatum.x;
      const dy = rect.height / 2 - nodeDatum.y;
      canvas.transition().duration(350).attr('transform', `translate(${{dx * 0.18}}, ${{dy * 0.12}})`);
    }}

    function closePanel() {{
      panel.classList.remove('open');
      panel.setAttribute('aria-hidden', 'true');
      storyMode = false;
      storyBtn.textContent = '▶ Restart Story';
      currentNode = null;
      selectedId = null;
      updateSelectionStyles();
      canvas.transition().duration(250).attr('transform', 'translate(0,0)');
    }}

    function goToStoryStep(delta) {{
      if (!currentNode || !currentNode.spineStep) return;
      const nextIndex = currentNode.spineStep - 1 + delta;
      if (nextIndex < 0 || nextIndex >= storyNodes.length) return;
      openNode(storyNodes[nextIndex], true);
    }}

    storyBtn.addEventListener('click', () => {{
      storyMode = true;
      openNode(storyNodes[0], true);
    }});

    nextBtn.addEventListener('click', () => {{
      if (!currentNode || !currentNode.nextNodeId) return;
      openNode(nodeById.get(currentNode.nextNodeId), true);
    }});

    closePanelBtn.addEventListener('click', closePanel);
    document.addEventListener('keydown', (event) => {{
      if (event.key === 'Escape' && panel.classList.contains('open')) {{
        closePanel();
      }} else if (event.key === 'ArrowRight' && panel.classList.contains('open')) {{
        goToStoryStep(1);
      }} else if (event.key === 'ArrowLeft' && panel.classList.contains('open')) {{
        goToStoryStep(-1);
      }}
    }});

    window.addEventListener('resize', () => {{ rect = sizeGraph(); }});
    updateSelectionStyles();
  </script>
</body>
</html>
"""


def main() -> None:
    texts, unreadable = read_sources()
    nodes, todo_map = build_nodes(texts)
    html = render_html(nodes, unreadable, todo_map)
    OUTPUT_HTML.write_text(html, encoding="utf-8")

    size_bytes = OUTPUT_HTML.stat().st_size
    synthesis_flags = [(n.title, n.synthesis_flag) for n in nodes if n.synthesis_flag]

    print(f"Final file size: {size_bytes:,} bytes")
    if unreadable:
        print("Source files you couldn't read:")
        for name, reason in unreadable:
            print(f"- {name}: {reason}")
    else:
        print("Source files you couldn't read: none")

    print("TODOs by node:")
    if todo_map:
        for title, items in todo_map.items():
            print(f"- {title}")
            for item in items:
                print(f"  - TODO: {item}")
    else:
        print("- none")

    print("Spine nodes with synthesis beyond sources:")
    if synthesis_flags:
        for title, note in synthesis_flags:
            print(f"- {title}: {note}")
    else:
        print("- none")


if __name__ == "__main__":
    main()
