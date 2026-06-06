# TAVSS — Team Talking Script (Final Presentation)

**MGT 599 Capstone · Group 4 · DePaul University**
**Deck:** `Group 4 TAVSS FINAL.pptx` (11 slides, presented in order) · **HARD CAP: 10:00** (demo included) · Q&A follows separately
**TAVSS = Taxonomy-Aware Venture Segmentation System**

> The honest version of the story: six months, ~250 hours, **17 documented model variants**, one number we killed on purpose, and a result we earned. Every figure is cross-checked (`TAVSS_DECK_AUDIT.md`). Say the numbers exactly as written. Mean every sentence.

---

## Speaker assignments & timing (sums to ~9:25 — protects the 10:00 cap)

| Slide | Speaker | Beat | Target |
|---|---|---|---|
| 1 Title | **Tserennadmid** | Hook + purpose | 0:25 |
| 2 Agenda | **Tserennadmid** | Plan + who does what | 0:30 |
| 3 Problems & Stakes | **Vishal** | Critical issue #1 | 0:45 |
| 4 Research | **Srilaxmi** | The three questions | 0:50 |
| 5 Data Foundation | **Vishal** | The foundation | 0:50 |
| 6 BreezeML & Models | **Akash** | What we built (illustration) | 1:05 |
| 7 The Mirage ★ | **Subasree** | Critical issue #2 — honesty | 1:15 |
| 8 The Climb | **Akash** | Quantitative progression | 0:45 |
| 9 Honest Verdict | **Subasree** | The earned result | 1:00 |
| 10 Built/Learned + Task 2 | **Tserennadmid** | Review + close | 1:15 |
| 11 Demo | **Akash** | Ending ties to purpose | 0:45 |
| **Total** | | | **~9:25** |

### Rubric coverage — built to hit all of it
- **Hook + purpose** → S1 · **Plan + division of labor** → S2 · **Critical issues** → S3, S7, S9 · **Quantitative data** → S6, S8, S9, S10 · **Illustrations/examples** → S6 (BreezeML), S4 (GECS anchors), S7 (mirage), S11 (live demo) · **Main points reviewed** → S10
- **Well-connected flow** → callbacks + named handoffs · **Ending ties to purpose** → S10 + S11 answer S1's question · **Lively tone / pauses** → cues in italics · **Time efficiency** → 9:25 plan, hard cap 10:00

### House rules
- Look at the panel, not the screen. Pause one breath before any percentage.
- Hand off by name (the `[HANDOFF]` cues). **Tserennadmid holds the clicker** start to finish — he opens, advances, and his last slide is 10; Akash drives the demo on 11 from the same machine.
- If you lose a line: stop, look up, continue. Silence reads as confidence.

---

# SLIDE 1 — TITLE *(Tserennadmid · 0:25)*

> "Good afternoon. We're Group 4. Our capstone started with one question: *can a machine read a company — just its description — and know what industry it belongs to?* It sounds simple. It is not. For six months we built a system to answer it honestly. We call it TAVSS. I'm Tserennadmid, here with Akash, Vishal, Subasree, and Srilaxmi."

`[HANDOFF: Tserennadmid → advance to Agenda]`

---

# SLIDE 2 — AGENDA *(Tserennadmid · 0:30)*

> "Here's our plan, and who owns what. I'll set up the problem with Vishal, who walks you through the data. Srilaxmi frames our research questions. Akash shows the library and the models he built. Subasree takes you through the audit that reset this project, and our honest result. Then I'll wrap up what we built and learned — and Akash finishes with a live demo. Five chapters. Ten minutes."

> *(The "who owns what" sentence is a graded item — say it clearly.)*

`[HANDOFF: Tserennadmid → Vishal]`

---

# SLIDE 3 — PROBLEMS & STAKES *(Vishal · 0:45)*

> "Thanks Tserennadmid. Morningstar classifies every public company on Earth into 145 industries — by hand. In our data that's 23,207 companies, 53,585 segment records. Three problems. *(pause)* It doesn't scale — every IPO and spinoff is more manual work. It's ambiguous — 35 percent of companies are conglomerates, so 55 percent of our rows carry built-in label conflict. And it's expensive — these codes drive sector ETFs, benchmarks, and risk models. A misclassified conglomerate moves real money. Srilaxmi — what did we set out to prove?"

`[HANDOFF: Vishal → Srilaxmi]`

---

# SLIDE 4 — RESEARCH *(Srilaxmi · 0:50)*

> "Thanks Vishal. Three questions drove everything. One — can a transformer learn 145-class routing when we test it the *honest* way, with no company in both train and test? Two — does thinking in a hierarchy — sector, group, industry — beat a flat 145-way guess? Three — what's the real ceiling, and can we be honest about the gap? *(pause)* And one principle underneath all three: every prediction is grounded in Morningstar's own 2019 GECS definitions — we parsed all 145 of them straight from your taxonomy document. We didn't want the model inventing categories. We wanted it answering to yours. Vishal will show you the foundation we built on."

`[HANDOFF: Srilaxmi → Vishal]`

---

# SLIDE 5 — DATA FOUNDATION *(Vishal · 0:50)*

> "The input is a company's LongProfile, plus its segment names and descriptions. Four stages from raw to ready. *(point across)* 53,585 raw rows. Cleaned and deduplicated. Then the step that mattered most — enrichment: we fuse the profile with the segment that actually earns the revenue, so the model sees what an analyst sees. And the split — 42,116 train, 10,535 test — built so no company ever lands on both sides. That one rule is the reason every number you're about to hear is real. Akash — what did we build on top of this?"

`[HANDOFF: Vishal → Akash]`

---

# SLIDE 6 — BREEZEML & MODELS *(Akash · 1:05)*

> "Thanks Vishal. Most teams *use* libraries. We *shipped* one. *(pause)* This is `breezeml` — `pip install breezeml`, live on PyPI right now, five public releases. When scikit-learn deadlocked on our text, most teams would switch models. We found the support-vector math was wrong for our data shape, patched the upstream library, and cut training from twenty minutes to under two seconds. A later release added balanced class weights, so we could drop oversampling entirely. *(pause)* That library is the engine under TAVSS — it turns company text into vectors and routes them through the hierarchy. It outlives this capstone; anyone here can install it tonight. But building the engine wasn't the hard part. Subasree will tell you what we found when we checked our own work."

`[HANDOFF: Akash → Subasree]`

---

# SLIDE 7 — THE MIRAGE ★ *(Subasree · 1:15)* — SLOW DOWN, THIS IS THE HEART

> "Thank you, Akash. Early on, our model reported 88.9 percent. *(pause — let it land)* It looked legendary. We had a demo, high confidence scores, the works. And something felt wrong. So we audited our own data. *(pause)* 97.2 percent of our test rows had already been seen in training. The same company sat on both sides of the split. The 88.9 wasn't a result — it was the model remembering, not learning. *(pause)* We had a choice. Keep the number — nobody outside this room would ever know — or kill it. We killed it. We documented the leak with exact row counts, rebuilt every split company-disjoint, and re-baselined at an honest 59.65. *(pause)* Walking a number *down* by thirty points, on purpose, is the hardest and proudest thing this team did — because everything after it is real. Akash — show them the honest climb."

`[HANDOFF: Subasree → Akash]`

---

# SLIDE 8 — THE CLIMB *(Akash · 0:45)*

> "So we rebuilt, and we climbed again — honestly this time, logging all seventeen versions. From a true 59.65 percent with TF-IDF, up through twelve stacked classical models at 68, ModernBERT-base at 67, a single ModernBERT-large at 70.29 on dev — and finally a calibrated four-model ensemble. *(pause)* Every step here is earned on data where no company appears twice. Subasree — where did honest land us?"

`[HANDOFF: Akash → Subasree]`

---

# SLIDE 9 — HONEST VERDICT *(Subasree · 1:00)*

> "Here. *(pause)* On strictly company-disjoint data, our ensemble reaches 75.0 percent macro F1 and 91.4 percent top-3. *(pause)* That number isn't arbitrary — Morningstar's bar for this project was 0.75. We climbed from an honest 59 back to it without ever fooling ourselves again. And we stayed disciplined: cross-validation confirmed it, and a test-tuned 77.5 that *wouldn't* generalize we left on the table. *(pause)* Two lessons live here. The audit *was* the work — methodology is a deliverable. And the ceiling is in the data, not the model — half our rows are genuinely ambiguous. So our advice to the RED team: show analysts the top-3 as suggestions, and send the true conglomerates to a human. Tserennadmid will bring it home."

`[HANDOFF: Subasree → Tserennadmid]`

---

# SLIDE 10 — WHAT WE BUILT / LEARNED + TASK 2 *(Tserennadmid · 1:15)*

> "Thanks Subasree. Here's what we built. A TAVSS engine at an honest 75 percent on Task 1 — industry classification. The `breezeml` library. A hierarchy-first architecture. And a working product.
>
> *(TASK 2 — say it; it's not on the slide)* The case asked for two models. Task 1 is industry — the 75 percent. **Task 2 is subindustry** — 428 finer codes. We reused Task 1 to route a company to its industry at 88 percent, then a small specialist picks among just the one-to-thirteen subindustries under it — turning a 428-way problem into a 3-way one. That reaches **55 percent macro F1**, 19 points over a fine-tuned transformer, and it's our recommended next step.
>
> *(LEARNED + CLOSE — tie back to the opening)* Three things we'll keep: audit your own numbers before anyone else does; the data ceiling beats the model every time; and honesty is a competitive advantage — it's the only reason we trust our own 75. *(pause)* So — can a machine read a company and know its industry? Yes. Honestly, 75 percent of the time, and it tells you when it isn't sure. We met Morningstar's bar without lying to ourselves to get there. Akash will show you it's real."

`[HANDOFF: Tserennadmid → Akash, advance to demo]`

---

# SLIDE 11 — DEMO *(Akash · 0:45 + demo)*

> *(Akash runs the live demo — plain-English description in → Morningstar industry code, label, confidence, and the cascade path out. Land the point: it shows its work and flags its own uncertainty.)*

> "*(after the demo)* That's TAVSS — sub-second, reproducible, and honest about what it doesn't know. We're Tserennadmid, Akash, Vishal, Subasree, and Srilaxmi. Thank you — we'd love your questions."

`[OPEN Q&A]`

---

# IF YOU'RE RUNNING LONG (protect the 10:00 cap)

Trim in this order — never the audit:
1. Slide 6: drop the "outlives this capstone" line.
2. Slide 10: cut the Task 2 mechanism to one sentence ("a 428-way problem becomes a 3-way one — 55 percent macro F1").
**Do not cut Slide 7.** It is the reason the rest of the talk is credible.

---

# Q&A PREP (after the clock stops)

**Q — "Did you meet the success criteria?"** *(Subasree)*
> Primary bar, macro F1 ≥ 0.75 — met, at 75.0 on company-disjoint data. The second, F1 > 0.85 on the top-10 classes, we haven't cleared yet; that's bound up in the conglomerate ambiguity, and it's in our next steps.

**Q — "88.9 to 75 — did you regress?"** *(Subasree)*
> No — we got honest. The 88.9 was leakage: 97 percent of test rows were seen in training. We documented it, rebuilt company-disjoint splits, and re-baselined. 75 is reproducible where no company appears twice.

**Q — "Is the 75 overfit from calibration?"** *(Akash)*
> We checked. Uncalibrated is 73.95, five-fold CV is 73.96, and a test-tuned 77.5 we refused to headline because it won't generalize. We report 75 with all of that disclosed.

**Q — "What about Task 2?"** *(Tserennadmid)*
> Hybrid cascade — route to the industry at 88 percent, then pick among 1–13 subindustries. 55 percent macro F1, 19 points over a fine-tuned DeBERTa baseline, closing most of the gap to the 62 percent oracle ceiling. A finance-domain transformer is in progress.

**Q — "Why ModernBERT, not GPT-4 / Claude?"** *(Akash)*
> Closed-stack project — no external APIs, for fair, reproducible evaluation. ModernBERT fits the full profile and runs on one GPU in production.

**Q — "How is this different from what Morningstar does today?"** *(Vishal / Tserennadmid)*
> Their process is manual and inconsistent across analysts. TAVSS is reproducible, sub-second, and audited — it doesn't replace the analyst, it gives them a confidence-scored starting point so they spend their time on the genuinely ambiguous 35 percent.

> ⚠️ **Do NOT** repeat the old line "beats DeBERTa by +24.9pp" — it used the retracted 88.9% and isn't defensible.

---

# REHEARSAL CHECKLIST

- [ ] Each speaker reads their part aloud twice with a stopwatch; full team run-through once with handoffs
- [ ] **Time the full run — if over 10:00, apply the trim list above**
- [ ] Deck opens on the presentation machine; fonts render; demo pre-loaded by Akash
- [ ] Slide fixes applied (`TAVSS_DECK_AUDIT.md`): image-baked `rod_team`→`red_team`, `pypi_releases`, `breezeml-0.2.5` still to do in the design tool
- [ ] One printed copy of this script per speaker (laptop-failure backup)
