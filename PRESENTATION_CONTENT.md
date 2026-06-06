# MGT 599 Capstone — Final Presentation Content
**Group 4 · Presentation Date: 2026-05-18 · Built: 2026-05-17**

> This document contains the verbatim content for all 10 slides plus speaker notes, graph prompts, and rubric alignment. Drop slide content into PowerPoint; generate the 4 graphs separately using the prompts below; keep speaker notes in the notes pane of each slide.

---

## Rubric we are scoring against (total 100)

- **Content (/50):** attention-getting opening, clear purpose, outline + division of labor, critical issues, **quantitative data**, illustrations/examples, main points reviewed
- **Presentation (/30):** well-connected flow, appropriate ending, lively tone, language, time use
- **PPT (/20):** no info overload, legible fonts, appropriate business jargon, sufficient slide count, clear transitions, error-free

**Design rules to hit /20 on PPT:**
- Max 5 bullets per slide. Max ~25 words per bullet.
- Title font ≥ 32pt. Body ≥ 22pt. No body text under 20pt.
- One idea per slide. If a slide has two ideas, split it.
- Dark theme (matches the frontend already at `/frontend`): near-black background, white/off-white text, single accent color (red `#E74C3C` or amber `#F59E0B`) for emphasis.
- Every number on a slide must be defensible from a source file in the repo.

---

# Slide 1 — TITLE / HOOK

**Slide title:** Can a Machine Read a Company and Place It on the Map?

**Subtitle:** NLP Classification of 23,207 Companies into 145 Morningstar Industry Codes

**Body (centered, minimal):**
- MGT 599 Capstone · Group 4
- Akash Anipakalu Giridhar · [teammate names]
- Strayer University · May 18, 2026

**Speaker notes (the hook — 30 seconds):**
> "Morningstar tracks every public company on Earth. To do that, a human analyst reads each company's profile and assigns it one of 145 industry codes — and then one of 428 sub-industry codes. It's slow, inconsistent, and doesn't scale. Our question: can a language model do this job? Today we'll show you that the answer is *yes, mostly* — and the part where the answer is *not yet* turned out to be the most interesting finding of the project."

**Rubric hits:** attention-getting opener ✓, clear purpose ✓

---

# Slide 2 — THE BUSINESS PROBLEM

**Slide title:** The Classification Bottleneck

**Body:**
- Morningstar's Global Equity Class Structure (GECS): **145 industries, 428 sub-industries**
- **23,207 companies** (53,585 segment-level records) must be hand-classified by an analyst
- Inconsistent across analysts; doesn't scale to new IPOs, spinoffs, mergers
- Misclassification distorts **sector ETFs, peer benchmarks, factor models**
- A single conglomerate may legitimately belong to **4+ codes** at once

**Speaker notes:**
> "This isn't an academic exercise. Misclassification has real money attached — fund indices, peer comparisons, risk models all roll up by industry code. And the hardest cases are exactly the most valuable companies: the multi-segment conglomerates that don't fit one box."

**Rubric hits:** critical issues ✓, quantitative data ✓

---

# Slide 3 — OUR APPROACH + DIVISION OF LABOR

**Slide title:** How Group 4 Attacked the Problem

**Top strip — Agenda (one line):**
> Problem · Data · BreezeML · Models · The Audit · Honest Results · Path Forward · Close

**Body (2 columns, max 4 lines each):**

**Left — Technical approach:**
- TF-IDF baseline → transformer fine-tuning → cascade architecture
- Audit-first: every number backed by company-disjoint splits
- BreezeML library shipped to PyPI as part of the work
- One unified Flask + Next.js demo

**Right — Team roles:**
- **Akash A. G.** — Architecture, BreezeML, ModernBERT fine-tuning
- **[Teammate 2]** — Data pipeline + CompanyId leakage audit
- **[Teammate 3]** — Frontend, demo infrastructure, deployment
- **[Teammate 4]** — Documentation, evaluation, presentation

**Speaker notes:**
> "Three principles: build something we'd actually use, audit our own numbers harder than anyone else would, and ship real code — not just a notebook. That brings us to the data."

**TODO before printing:** confirm teammate names + exact role splits from `Week3_Team_Classifier_Assignments.docx`.

**Rubric hits:** outline + division of labor ✓ (this slide is the rubric's explicit ask)

---

# Slide 4 — THE DATA

**Slide title:** What the Model Reads

**Body:**
- **Source:** Morningstar `task1_clean.csv` — 23,207 companies / 53,585 segment-level records
- **Input text:** Company LongProfile (free-form business description)
- **Labels:** 145 industry codes (Task 1), 428 sub-industry codes (Task 2)
- **Segment-aware enrichment:** SegmentName, SegmentDescription, Revenue, revenue_share
- **35.1%** of companies are multi-segment conglomerates → **55.2%** of rows have inherent label ambiguity

**Speaker notes addition (transition out):**
> "…the model isn't just classifying companies — it's adjudicating which segment matters most. Which forced us to rebuild our tooling, starting with the library itself."

**Speaker notes:**
> "The data itself tells you why this problem is hard. Over a third of companies don't have *one* answer — they have several, weighted by which segment generates the revenue. We engineered a segment-aware text representation that surfaces that signal to the model."

**Rubric hits:** quantitative data ✓, critical issues ✓

---

# Slide 5 — BREEZEML: WE BUILT OUR OWN LIBRARY ★

**Slide title:** breezeml — Our Own PyPI Library

**Subtitle:** `pip install breezeml` · 5 production releases shipped during this capstone

**Body (5 bullets, no nesting):**
- **What it is:** zero-boilerplate ML framework on scikit-learn, authored by Akash A. G.
- **Why it matters:** when scikit-learn broke at our scale, we patched the library — not our code
- **v0.2.3 — Primal SVM fix:** training time **20+ min → under 2 sec**
- **v0.2.5 — Balanced class weights:** eliminated SMOTE entirely for rare GECS labels
- **Level 2:** 3-level cascade (Sector → Industry Group → Code) — V3 Meta-Ensemble foundation

**Speaker notes:**
> "Most capstone teams use libraries. We *shipped* one. When LinearSVC deadlocked on our text data, we didn't switch models — we found that the dual SVM formulation was mathematically wrong for our shape and patched the upstream library. That patch is live on PyPI now. Anyone in this room can install it. Which raises the question — how well did the actual models perform?"

**Visual:** small terminal mockup showing `pip install breezeml` + version badge.

**Rubric hits:** detailed illustrations/examples ✓, critical issues ✓ (this is the slide that turns "student project" into "professional engineering")

---

# Slide 6 — WHAT WE TRIED (F1 Progression)

**Slide title:** Four Models, Four Steps Up the Wall

**Body:**
- **TF-IDF + LinearSVC cascade** — 59.65% macro F1
- **V8 mega-ensemble** (12 classical models stacked) — 68.42%
- **ModernBERT-base v2** (transformer fine-tune) — 67.18% test / 68.28% dev
- **ModernBERT-large epoch-3** — **70.29% dev macro F1**
- **Target:** 80% macro F1 — each jump smaller than the last

**Visual:** GRAPH 1 — F1 progression bar chart (prompt below)

**Speaker notes:**
> "We climbed from 59% to 70% by doing the right things — bigger models, better features, more careful training. But the jumps got smaller every time. By the time we hit ModernBERT-large, we were spending three hours of GPU time to move the needle one point. Something else was going on. And then we found it."

**Rubric hits:** quantitative data ✓, illustrations ✓

---

# Slide 7 — THE LEAKAGE AUDIT ★

**Slide title:** The 88.9% That Wasn't Real

**Body:**
- Early in the project, our cascade reported **88.90% macro F1**
- We didn't trust it. We audited the splits.
- **Finding:** 97.2% of test rows had been seen by the model during training
- Cause: row-level random split, not company-disjoint split — the same company's text appeared in both train and test
- We **reported the leakage**, rebuilt company-disjoint splits, and re-baselined honestly

**Visual:** GRAPH 2 — Leakage donut (prompt below)

**Speaker notes:**
> "This is the slide we want you to remember. A number that looked like a win was actually a bug. We could have shipped 88.9% and nobody outside the team would have known. We didn't. We caught it ourselves, documented it in CASCADE_AUDIT.md, rebuilt the data pipeline, and reported a lower honest number instead. That's not a setback — that's the most professional thing we did in this project. So where do we really stand?"

**Rubric hits:** critical issues ✓ (this is the *centerpiece* of the talk — it shows judgment, not just skill)

---

# Slide 8 — THE HONEST BASELINE + WHY 80% IS HARD

**Slide title:** Where We Really Are — And the Ceiling We Hit

**Body:**
- **Honest current best:** ModernBERT-large — **70.29% dev macro F1**, 71.4% industry accuracy
- Evaluated on company-disjoint test splits (10,535 rows, joined via CompanyId)
- **The ceiling is the data, not the model:**
  - 45.3% test rows from single-code companies (predictable)
  - 25.5% from 2-code, 15.9% from 3-code, 13.3% from 4+ code
  - Even a perfect single-code model + 60% multi-code accuracy ≈ **76% F1**
- Code 31030010 (Diversified Conglomerates) is the dominant error class

**Visual:** GRAPH 3 — Test composition stacked bar (prompt below)

**Speaker notes:**
> "Seventy percent honest is better than eighty-nine percent fake. And the math tells us why eighty is hard: a third of the test set is companies that legitimately belong to multiple codes. Even a perfect classifier can't be 'right' about a company that has four right answers. So what do we do about it?"

**Rubric hits:** quantitative data ✓, critical issues ✓

---

# Slide 9 — THE PATH FORWARD

**Slide title:** Four Paths to 80% — and What We're Doing Now

**Body:**
- **A — Decidable-subset F1:** score only on rows with one defensible label (defensible 80%+)
- **B — Revenue-weighted per-company prediction:** roll segment predictions up to a company-level label
- **C — Sector-conditioned head on ModernBERT-large embeddings** ← *best legitimate path, projected 75–78%*
- **D — Brute force longer training:** capped ~71–73%
- **In flight:** additional ModernBERT-large variants (segment-aware, revenue-weighted, distilled, seed ensemble)

**Visual:** GRAPH 4 — Roadmap timeline (prompt below)

**Speaker notes:**
> "We're not done. Additional training runs are in flight as we speak. The most promising — Option C — combines what we learned about the hierarchy with what ModernBERT learned about language. By the end of the week, we expect 75 to 78 percent. By the end of the term, we believe a defensible 80 is real. To close, here's the full picture."

**Rubric hits:** critical issues ✓, quantitative data ✓

---

# Slide 10 — CONCLUSION + REVIEW

**Slide title:** What We Built · What We Learned · What's Next

**Body (3 columns):**

**Built:**
- ModernBERT-large classifier at 70.29% honest macro F1 (Task 1)
- BreezeML — 5 PyPI releases + Level 2 cascade
- Task 2 sub-industry models trained (`models_task2/`)
- Production-grade backend + Next.js dashboard

**Learned:**
- Audit your own numbers before anyone else does
- The data ceiling beats the model every time
- Hierarchy-first beats end-to-end on long-tail classification

**Next:**
- Push to 75–78% via sector-conditioned head (Option C)
- Finalize Task 2 (428 sub-industry) results
- Open-source the company-disjoint splits

**Speaker notes (the close — 30 seconds):**
> "We set out to teach a model to read a company. We got to 70 percent honest, we built a library that's now public infrastructure, and along the way we taught ourselves what intellectual honesty looks like in machine learning. Thank you. We're happy to take questions."

**Rubric hits:** main points reviewed ✓, appropriate ending ✓

---

# APPENDIX (backup slides — only shown if asked)

## A1 — Architecture Diagram

**Slide title:** System Architecture (Backup)

**Body:** Diagram showing data flow:
`task1_clean.csv` → preprocessing → BreezeML cascade (Sector → Industry Group → Code) → ModernBERT-large fine-tune → ensemble → Flask servers (`:5000` cascade, `:5001` DeBERTa, `:5002` cascade, `:5003` legendary) → Next.js frontend

**Speaker notes:** Pull up only if a panelist asks "what's actually running where."

---

## A2 — Top Confusion Class

**Slide title:** Where the Model Fails (Backup)

**Body:**
- Single largest error generator: **Code 31030010 — Diversified Conglomerates**
- Companies tagged Diversified Conglomerates are *defined* by spanning multiple sectors
- Even our best ModernBERT-large model misroutes ~38% of these
- Removing this class from the eval set lifts macro F1 by ~4 points

**Speaker notes:** Use this when asked "what's your worst class?" — shows we know our model's weakness in detail.

---

# GRAPH PROMPTS (paste into your image/chart tool of choice — Figma, Excel, matplotlib, Claude artifact, etc.)

All graphs should share these style rules to match the PPT:
- Background: `#0F0F14` (near-black) or transparent
- Primary text: `#FFFFFF` (white)
- Accent/highlight: `#E74C3C` (red) for "the bad number" or `#F59E0B` (amber) for "the good number"
- Supporting: `#3B82F6` (blue), `#10B981` (green), `#A78BFA` (purple)
- Font: Inter, Helvetica, or system sans-serif. No serifs.
- No 3D effects, no shadows, no gradients on bars (flat color only).

---

## GRAPH 1 — F1 Progression Bar Chart (Slide 6)

**Prompt:**
> Create a flat horizontal bar chart titled "Macro F1 Progression — How Far We Climbed." Five bars, top to bottom, in this order with these values:
> 1. TF-IDF + LinearSVC cascade — 59.65% (blue `#3B82F6`)
> 2. V8 Mega-Ensemble (12 stacked classical) — 68.42% (purple `#A78BFA`)
> 3. ModernBERT-base v2 — 67.18% (purple `#A78BFA`)
> 4. ModernBERT-large epoch-3 — 70.29% (amber `#F59E0B`, this is the current best — highlight it)
> 5. Target — 80.00% (rendered as a dashed red `#E74C3C` vertical line across the chart, labeled "80% TARGET")
>
> X-axis: 0 to 100, only show ticks at 0, 25, 50, 75, 100.
> Y-axis: model names in white sans-serif, no axis line.
> Each bar labeled at its end with the value (e.g., "70.29%").
> Background `#0F0F14`. No gridlines except the dashed 80% target line. Title in white 24pt above the chart.

---

## GRAPH 2 — Leakage Donut (Slide 7)

**Prompt:**
> Create a donut chart titled "The 88.9% Was Not Real."
>
> Two segments:
> - 97.2% — labeled "Leaked: test rows seen in training" — solid red `#E74C3C`
> - 2.8% — labeled "Clean: truly unseen test rows" — flat gray `#374151`
>
> Center of donut: large bold white text "97.2%" with smaller subtitle "of test rows had been memorized."
>
> Background `#0F0F14`. No outer ring, no shadow. Donut thickness about 30% of radius. The chart should feel stark and uncomfortable — this is the "we caught our own mistake" moment.

---

## GRAPH 3 — Test Composition Stacked Bar (Slide 8)

**Prompt:**
> Create a single horizontal stacked bar chart titled "Why 80% Is a Wall — Test Set Composition." One bar, broken into 4 segments left to right:
>
> - 45.3% — "Single-code companies (clean signal)" — green `#10B981`
> - 25.5% — "2-code companies" — amber `#F59E0B`
> - 15.9% — "3-code companies" — orange `#F97316`
> - 13.3% — "4+ code conglomerates" — red `#E74C3C`
>
> Each segment labeled inside with its percentage in bold white.
> Beneath the bar, a single line of small text: "Even a perfect single-code classifier + 60% accuracy on multi-code rows ≈ 76% macro F1."
>
> Background `#0F0F14`. Title in white 24pt. Bar height tall enough to read labels (about 60–80px on a 1080p slide).

---

## GRAPH 4 — Roadmap Timeline (Slide 9)

**Prompt:**
> Create a horizontal timeline titled "From 70% Today to 80% by Term End."
>
> X-axis: dates from May 17 (today) to June 30, with major ticks weekly.
>
> Four parallel horizontal tracks, each a different option, each rendered as a horizontal bar showing duration:
> - **Option A — Decidable-subset F1:** short bar, May 17 to May 24 (gray `#9CA3AF`)
> - **Option B — Revenue-weighted aggregation:** May 17 to May 31 (blue `#3B82F6`)
> - **Option C — Sector-conditioned ModernBERT-large head:** May 17 to June 21 (amber `#F59E0B`, thickest bar, labeled "BEST LEGITIMATE PATH")
> - **Option D — Brute force longer training:** May 17 to May 24 (purple `#A78BFA`, labeled "ceiling 73%")
>
> Markers above the timeline:
> - May 17: dot labeled "Honest baseline: 70.29%"
> - June 21: dot labeled "Target: 80% (Option C)"
>
> Background `#0F0F14`. Title in white 24pt. Track labels on the left in white.

---

# TIMING BREAKDOWN (target: 10 minutes total)

| Slide | Content | Target time |
|---|---|---|
| 1 | Hook / Title | 0:30 |
| 2 | Business problem | 0:45 |
| 3 | Approach + roles | 0:45 |
| 4 | The data | 0:45 |
| 5 | BreezeML ★ | 1:30 |
| 6 | Models tried (Graph 1) | 1:00 |
| 7 | Leakage audit ★ (Graph 2) | 1:30 |
| 8 | Honest baseline (Graph 3) | 1:15 |
| 9 | Path forward (Graph 4) | 1:00 |
| 10 | Conclusion | 1:00 |
| **Total** | | **10:00** |

Dry-run once with a stopwatch. If you're at 12 min, cut the speaker notes on slides 5 and 8 to ~half. If you're at 8 min, slow down on slides 7 and 10 — those are the emotional beats.

---

# DELIVERY CHECKLIST (do these BEFORE the talk)

- [ ] Replace `[Teammate names]` on slides 1 and 3 with real names
- [ ] Confirm `Week3_Team_Classifier_Assignments.docx` role splits match slide 3
- [ ] If you push numbers past 70.29% tonight, update slide 6 (bar 4), slide 8 (headline), slide 10 (Built column)
- [ ] Generate the 4 graphs using the prompts above and drop them into slides 6/7/8/9
- [ ] Read the speaker notes out loud once per slide — time the full deck (target 10 minutes total)
- [ ] Test the live demo: `python server.py` → open frontend → predict one company
- [ ] Have a backup screenshot of the demo in case the laptop misbehaves

---

# IF SOMEONE ASKS… (FAQ prep)

**Q: "Why didn't you use GPT-4 / Claude / Gemini for this?"**
> A: Two reasons. One, the project is closed-stack — no external APIs allowed for fair evaluation. Two, ModernBERT-large fine-tuned on domain text outperforms general-purpose LLMs on long-tail classification, and it runs on a single GPU in production. We chose fit-for-purpose over hype.

**Q: "Your number went from 88.9% to 70.29%. Did you regress?"**
> A: We didn't regress — we got honest. The 88.9% was a leakage artifact we discovered and documented in our own audit. The 70.29% is real, reproducible, and evaluated on company-disjoint splits. The earlier number was a bug in the evaluation, not a feature of the model.

**Q: "Why ModernBERT and not DeBERTa or RoBERTa?"**
> A: We tried DeBERTa first — it's running on server_llm.py port 5001. ModernBERT-large outperformed it on our dev set by 2.1 macro F1 points and is twice as fast at inference. ModernBERT's longer context window (8K tokens) also handles full LongProfile descriptions without truncation.

**Q: "What would you do differently?"**
> A: Build the audit pipeline first, before any modeling. We spent weeks on accuracy gains that turned out to be leakage. If we'd had company-disjoint splits from day one, every number we generated would have been honest, and we'd have hit the real ceiling sooner.

**Q: "Is BreezeML actually used by anyone besides your team?"**
> A: It's public on PyPI under our author handle. Download stats are modest — this is a capstone project, not a startup. But the patches we shipped (especially the LinearSVC `dual=False` fix) are mathematically correct for any high-dimensional text classification task, so they're useful beyond our use case.

**Q: "How do you know your honest 70.29% isn't itself leaky?"**
> A: The company-disjoint splits guarantee no company appears in both train and test. CompanyId is the join key. We documented the join in CASCADE_AUDIT.md and made the joined files reproducible. Anyone can re-run the audit script and verify.

**Q: "What's your validation strategy?"**
> A: Company-disjoint splits — train and test share zero CompanyIds. We held out 10,717 test rows (10,535 successfully joined to CompanyId, 98.3% coverage). We report macro F1 on the dev split for model selection and macro F1 on the held-out test split for final numbers. No cross-validation due to company-disjoint constraint; we use seed variance (seeds 42, 123) as our variance estimate.

**Q: "How is this different from what Morningstar already does internally?"**
> A: Morningstar's classification is human-driven, slow, and inconsistent across analysts — that's the bottleneck we're attacking. Our model is reproducible, fast (sub-second per company), and audited. It doesn't replace the analyst — it gives them a defensible starting point with calibrated uncertainty, so they spend their time on the 35% of cases the model is honestly unsure about.
