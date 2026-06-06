# Mapping Market Reality — Team Talking Script
**MGT 599 Capstone · Group 4 · Presentation Day: May 18, 2026**
**Deck:** `Mapping_Market_Reality.pptx` (12 slides)
**Target runtime:** 10:00 · Q&A follows

---

## Speaker assignments (by stated project role)

| Speaker | Slides | Approx. minutes |
|---|---|---|
| **Toremohmd** — *Preprocessing, data cleaning, project continuity* | 1, 2, 3, 11, 12 | 2:50 |
| **Akash** — *Architecture, BreezeML, ModernBERT* | 4, 6, 10 | 2:45 |
| **Vishal** — *Feature engineering, TF-IDF, sparse vectors* | 5, 7 | 1:50 |
| **Subasree** — *Evaluation, diagnostics, results synthesis* | 8, 9 | 2:45 |

**House rules for delivery:**
- Read once with a stopwatch tonight. Adjust pace, not content.
- Look at the panel, not the screen. The slide is behind you; trust it.
- Hand off explicitly: *"…and Akash will take it from here."* The bracketed cue at the bottom of each slide is the handoff signal.
- Pause for one full breath before saying any number that ends in a percent sign. Numbers are the strongest moments.
- If you forget a line, stop. Look up. Continue. Silence is not a failure.

---

# SLIDE 1 — TITLE *(Toremohmd · 0:30)*

> "Good afternoon. Our team is Group 4, and our capstone asks a single question — can a machine read a company description and know what industry it belongs to? That sounds simple. It is not. Today we'll walk you through six months of work answering it: the problem we set out to solve, the data foundation we built, the moment our results turned out to be too good to be true, and the honest baseline we now stand on. I'm Toremohmd. Joining me are Akash, Vishal, and Subasree."

`[HANDOFF: Toremohmd → Toremohmd, advance to Agenda]`

---

# SLIDE 2 — AGENDA *(Toremohmd · 0:30)*

> "Here's how we'll move. I'll set up the problem and the data. Akash will walk you through the pipeline we built, including the open-source library we authored along the way. Vishal will show you the four models we trained and the wall we hit. Subasree will take you through the audit moment that reshaped this project. Then Akash returns with the path forward, and I'll close with what we built, what we learned, and what comes next."

`[HANDOFF: Toremohmd → Toremohmd, advance to Slide 3]`

---

# SLIDE 3 — THE PROBLEM *(Toremohmd · 0:45)*

> "Morningstar classifies every public company on Earth into one of 145 industries and 428 sub-industries. In our dataset, that's 23,207 unique companies spread across 53,585 segment-level records. Right now, that classification happens by hand. Analysts read each company's profile and assign a code. It's slow, it's inconsistent between analysts, and it doesn't scale to IPOs, spinoffs, or mergers. And it has real money attached — sector ETFs, peer benchmarks, factor models all roll up from these codes. A misclassified conglomerate distorts the index. Akash will explain how we built a system to do this work automatically."

`[HANDOFF: Toremohmd → Akash]`

---

# SLIDE 4 — THE PIPELINE + TEAM *(Akash · 0:45)*

> "Thanks Toremohmd. Three principles guided how we built this. First — hierarchy-first. We don't ask the model to choose between 145 classes at once. We route Sector to Industry Group to Code, the way an analyst actually thinks. Second — audit-first. Every number you'll see today is backed by a strict company-disjoint test split. Third — taxonomy-grounded. Our predictions are anchored to Morningstar's 2019 GECS definitions, not to whatever the model decides to invent. On the team side: I own architecture, the BreezeML library, and the ModernBERT fine-tuning. Subasree owns evaluation. Vishal owns feature engineering. Toremohmd owns the data pipeline and repo. Vishal will tell you what the data looks like."

`[HANDOFF: Akash → Vishal]`

---

# SLIDE 5 — DATA FOUNDATION *(Vishal · 0:50)*

> "Thanks Akash. The raw input to our system is a company's LongProfile — a free-form, unstructured business description. That alone isn't enough, because of one fact that drove most of our engineering decisions: 35.1 percent of companies in our dataset are multi-segment conglomerates. One company, multiple legitimate industry codes. That means 55.2 percent of our database rows have inherent label ambiguity built in. So we built an enrichment layer on top of the LongProfile — adding SegmentName, SegmentDescription, Revenue, and revenue share. This gives the model what an analyst sees: not just what the company is, but which segment actually makes the money. Akash will show you the library we built to make this possible."

`[HANDOFF: Vishal → Akash]`

---

# SLIDE 6 — BREEZEML ★ *(Akash · 1:15)*

> "Most capstone teams use libraries. We shipped one. *(pause)* This is `breezeml` — `pip install breezeml`. It's a zero-boilerplate machine learning framework I authored on top of scikit-learn, and it's live on PyPI right now. Anyone in this room can install it. We didn't just write it once. We shipped five public releases during this project. The most important one — version 0.2.3 — was a primal SVM fix. The library was deadlocking on our text data because of how scikit-learn solved the support vector formulation. Most teams would have switched models. We diagnosed the math, patched the upstream library, and brought training time from over twenty minutes down to under two seconds. Version 0.2.5 added balanced class weights for the rare GECS labels, which eliminated the need for SMOTE oversampling entirely. The result is a public library that any future analyst can install — including the panel — and replicate our preprocessing in one line. Vishal will walk you through what we did with it."

`[HANDOFF: Akash → Vishal]`

---

# SLIDE 7 — FOUR MODELS, FOUR STEPS *(Vishal · 1:00)*

> "We climbed this wall in four steps. Our TF-IDF cascade with LinearSVC got us to 59.65 percent macro F1. Stacking twelve classical models in our V8 mega-ensemble took us to 68.42. We then moved to transformers — ModernBERT-base v2 landed at 67.18 percent. And our current honest best, ModernBERT-large at epoch three, is 70.29 percent macro F1. The target — the gold line you see across the chart — is 80 percent. *(pause)* Notice the shape of the climb. Each jump is smaller than the last. By the time we hit ModernBERT-large, three hours of GPU time was buying us a single point of macro F1. Something else was happening — and Subasree will tell you what we found."

`[HANDOFF: Vishal → Subasree]`

---

# SLIDE 8 — THE MIRAGE ★ *(Subasree · 1:30)*

> "Thank you Vishal. Earlier in this project, our cascade reported 88.9 percent macro F1. That's the number on this slide — the one with the red strikethrough. *(pause)* We did not trust it. So we audited the data. And what we found was this: 97.2 percent of our test rows had already been seen by the model during training. The same company's text appeared on both sides of the train-test split, because the original split was randomized at the row level, not at the company level. The 88.9 was not a result. It was a leak. *(pause)* Three things happened next. We acknowledged it. We documented it in a file called CASCADE_AUDIT.md, with the exact join logic and contaminated row counts. And we rebuilt the entire evaluation pipeline on a strict company-disjoint basis — meaning no company ever appears in both train and test again. We could have published the 88.9. Nobody outside this team would have caught it. That decision to report a lower honest number is, in my view, the most professional thing this team did in the entire capstone."

`[HANDOFF: Subasree → Subasree, advance to Slide 9]`

---

# SLIDE 9 — THE HONEST BASELINE + CEILING *(Subasree · 1:15)*

> "Here is where we actually stand. ModernBERT-large fine-tuned on the company-disjoint splits delivers 70.29 percent dev macro F1. That number is reproducible, it is auditable, and it is the bar from which everything we do next will be measured. But notice the chart on the right. Our test set is 45.3 percent single-code companies, 25.5 percent two-code, 15.9 percent three-code, and 13.3 percent four-or-more-code conglomerates. Even a hypothetical perfect classifier on the single-code rows, combined with 60 percent accuracy on the multi-code rows, mathematically caps macro F1 at approximately 76 percent. *(pause)* In other words: the gap from 70 to 80 percent is not a model problem. It is a data problem. The ceiling is structural. Akash will show you the four strategies we're using to attack it."

`[HANDOFF: Subasree → Akash]`

---

# SLIDE 10 — FOUR PATHS *(Akash · 0:45)*

> "We have four paths forward. Path A — the decidable-subset approach — scores models only on rows with one unambiguous label, bypassing the conglomerate ceiling. Path B rolls segment-level predictions up to company-level via revenue weighting. Path D extends ModernBERT training with longer schedules — but the data confirms that route caps near 73 percent. *(pause and point to Path C)* The path we believe in is C. We apply a hierarchical routing head directly onto ModernBERT-large embeddings — a fusion of the cascade architecture and the transformer's representational power. This run is in flight right now, and our projection is 75 to 78 percent macro F1 by term end. Toremohmd will close us out."

`[HANDOFF: Akash → Toremohmd]`

---

# SLIDE 11 — WHAT WE BUILT · WHAT WE LEARNED *(Toremohmd · 0:45)*

> "Here is what we built. A ModernBERT-large classifier running at an honest 70.29 percent macro F1. The `breezeml` library, with five successful PyPI releases. Task 2 — the 428 sub-industry models — successfully trained across all distinct codes. And a production-ready backend with a unified Next.js dashboard. *(pause)* Here is what we learned. Audit your own numbers, relentlessly, before anyone else does. The structural data ceiling will beat the mathematical model every single time. And a hierarchy-first architecture, consistently, defeats end-to-end processing on long-tail classification problems. *(pause)* If we leave you with one sentence, it's this: industry classification is not one hundred percent automatable. The resulting product is an analyst-first system, designed to handle the obvious cases, defer on the ambiguous conglomerates, and log every prediction against the truth."

`[HANDOFF: Toremohmd → Toremohmd, advance to Slide 12]`

---

# SLIDE 12 — THANK YOU & QUESTIONS *(Toremohmd · 0:20)*

> "Three takeaways to remember. Data quality shapes model truth. Strict company-disjoint splits reveal reality. Path C — the hierarchical routing head — is the best legitimate path forward. *(pause)* Thank you. We are Akash, Subasree, Vishal, and Toremohmd. We are happy to take your questions."

`[OPEN Q&A]`

---

# RUNTIME CHECK

| Slide | Speaker | Target | Words | Pace |
|---|---|---|---|---|
| 1 | Toremohmd | 0:30 | ~80 | comfortable |
| 2 | Toremohmd | 0:30 | ~80 | comfortable |
| 3 | Toremohmd | 0:45 | ~115 | comfortable |
| 4 | Akash | 0:45 | ~130 | brisk |
| 5 | Vishal | 0:50 | ~135 | brisk |
| 6 | Akash | 1:15 | ~225 | normal |
| 7 | Vishal | 1:00 | ~155 | normal |
| 8 | Subasree | 1:30 | ~250 | normal — *the centerpiece, slow down* |
| 9 | Subasree | 1:15 | ~195 | normal |
| 10 | Akash | 0:45 | ~125 | brisk |
| 11 | Toremohmd | 0:45 | ~155 | brisk |
| 12 | Toremohmd | 0:20 | ~55 | comfortable |
| **Total** | | **~10:00** | | |

---

# Q&A PREP — six likely questions

**Q1 — "Why did the 88.9 percent number drop to 70?"** *(answer: Subasree)*
> The 88.9 was a leakage artifact. Our original splits were row-randomized, which let the same company's text appear in both train and test. We audited it, documented it in CASCADE_AUDIT.md, rebuilt the splits on a company-disjoint basis, and re-baselined. The 70.29 is reproducible on splits where no company appears in both halves.

**Q2 — "Why ModernBERT and not GPT-4 or Claude?"** *(answer: Akash)*
> Our project is closed-stack — no external APIs were permitted for fair evaluation. ModernBERT-large also outperformed DeBERTa on our dev set by 2.1 points and handles the full LongProfile in its 8K context window without truncation. It runs on a single GPU in production.

**Q3 — "What is your validation strategy?"** *(answer: Subasree)*
> Strict company-disjoint splits — CompanyId is the join key, and no company appears in both train and test. We hold out 10,535 of 10,717 test rows after CompanyId joining, which is 98.3 percent coverage. We report macro F1 on dev for model selection and macro F1 on the held-out test for final numbers.

**Q4 — "Is BreezeML actually used outside this project?"** *(answer: Akash)*
> It's public on PyPI. Adoption is modest — this is a capstone, not a startup — but the patches are mathematically correct for any high-dimensional text classification task, so they're useful beyond our scope.

**Q5 — "Why are you confident in 75–78 percent for Path C?"** *(answer: Akash)*
> Path C uses ModernBERT-large's embeddings as input to a hierarchical routing head trained on the GECS taxonomy. The 70.29 is what the model achieves when forced to choose among 145 classes flat. The hierarchical routing collapses the long-tail problem into successive smaller decisions, which is mathematically equivalent to giving the model the taxonomy structure as a prior. Empirical results from related work suggest 5 to 8 point gains.

**Q6 — "How is this different from what Morningstar already does internally?"** *(answer: Toremohmd or Vishal)*
> Morningstar's process is analyst-driven, slow, and inconsistent across humans. Our system is reproducible, sub-second per company, and audited end-to-end. It doesn't replace the analyst — it gives them a defensible starting point with calibrated uncertainty, so they spend their time on the 35 percent of cases where ambiguity is real.

---

# REHEARSAL CHECKLIST (do before walking in)

- [ ] Each person reads their slides aloud at least twice, with a stopwatch
- [ ] Full team walkthrough once, end-to-end, with handoff phrases practiced
- [ ] Confirm the deck file opens on the presentation machine
- [ ] Print this script (one copy per speaker) as backup if a laptop fails
- [ ] Decide who advances slides — recommend Toremohmd holds the clicker (he opens and closes; minimizes mid-deck handoff of the clicker)
- [ ] One team member opens `team_briefing.html` or the demo in a browser tab beforehand in case of a live-demo question
