# TAVSS Final Deck — Audit & Fact-Check

**Deck audited:** `Group 4 TAVSS FINAL.pptx` (11 slides, 16:9, saved 2026-05-27)
**Audited:** 2026-05-29 · for the Monday final presentation
**Cross-referenced against:** DePaul/Morningstar case brief (`Task Doc/DePaul_case_2026_Q2_RED_activity_case.pdf`), `WEEK_6_REPORT.md`, `WEEK_7_REPORT.md`, `CAPSTONE_FINAL_REPORT.md`, `docs/Task2_Hybrid_Cascade.docx`, `models_task2/t2_cascade_summary.json`, the final-presentation rubric, and the rendered slides.

> **TAVSS = Taxonomy-Aware Venture Segmentation System.**

---

## 0. Verdict at a glance

The deck is in good shape and tells an honest, well-structured story. The headline number (75.0% macro F1 / 91.4% top-3) is current and **clears the case's primary success bar of ≥0.75 macro F1 — exactly.** Most issues below are small consistency/spelling fixes. **Three things deserve real attention before Monday:**

1. **Slide 3 says "17,432 companies"** while the rest of the deck says **23,207**. One of these is wrong on the slide. (P1)
2. **Task 2 is not on any slide.** You're presenting it verbally — make sure the speaker owning it has the numbers cold (covered in the talking script). (P1)
3. **The case has a *second* success criterion** the deck doesn't address: **F1 > 0.85 on the top-10 most frequent classes.** Be ready for this in Q&A — it is not clearly met. (P1)

Priority key: **P1** = fix/prepare before Monday · **P2** = should fix · **P3** = polish.

---

## 1. The numbers — verified source of truth

These are the defensible figures, cross-checked across the case brief, weekly reports, and the final report. Use these everywhere.

### Problem / data (from the Morningstar case brief)
| Fact | Value | Source |
|---|---|---|
| Client | Morningstar Data Science + **RED** (Reference Entity Data) team | case brief |
| Task 1 | Industry classification — **145** GECS industries (`MstarGlobal`) | case brief |
| Task 2 | Subindustry / business activity — case says **"one of 450"**; **428** observed in data (**407** with samples) | case brief / `t2_cascade_summary.json` |
| Task 1 records | **53,585** | case brief |
| Task 2 records | **27,537** | case brief |
| Unique companies | **23,207** | weekly reports |
| Multi-segment companies | **35.1%** | reports |
| Rows with inherent label ambiguity | **55.2%** | reports |
| **Success criterion 1** | Macro-F1 **≥ 0.75** overall | case brief |
| **Success criterion 2** | F1 **> 0.85** on top-10 frequent classes | case brief |

### Task 1 results (current — Week 7, May 24)
| Metric | Value | Source |
|---|---|---|
| **Headline: macro F1** | **75.0%** (4-model ensemble, calibrated) | `WEEK_7_REPORT.md` |
| **Top-3 accuracy** | **91.4%** (91.49%) | `WEEK_7_REPORT.md` |
| Top-1 accuracy | 76.85% | `WEEK_7_REPORT.md` |
| Top-5 accuracy | 95.33% | `WEEK_7_REPORT.md` |
| Uncalibrated simple-mean ensemble | 73.95% | `WEEK_7_REPORT.md` |
| 5-fold cross-validated | 73.96% | `WEEK_7_REPORT.md` |
| Test-tuned upper bound (disclosed, not headline) | 77.51% | `WEEK_7_REPORT.md` |
| Presentation baseline (single ModernBERT-large, ep.3) | 70.29% dev / 71.4% acc | `WEEK_6_REPORT.md` |
| **Leaked (retracted) number** | **88.90%** (97.2% test rows seen in train) | `CASCADE_AUDIT.md` |

**Progression line (for slide 8):** TF-IDF+LinearSVC **59.65%** → V8 mega-ensemble **68.42%** → ModernBERT-base v2 **67.18% test / 68.28% dev** → ModernBERT-large **70.29% dev** → calibrated ensemble **75.0%**.

### Task 2 results (documented — Hybrid Cascade)
| Metric | Value | Source |
|---|---|---|
| **Macro F1** | **55.4%** (55.41% final report / 55.44% summary json) | `Task2_Hybrid_Cascade.docx`, `t2_cascade_summary.json` |
| Accuracy | ~74% (74.35% / 74.44%) | same |
| MSTAR routing accuracy (Task 1 inside cascade) | 88.42% | summary json |
| DeBERTa-v3-small baseline | 36.39% | both |
| Improvement over DeBERTa | +19.02 pp | final report |
| Oracle ceiling (if routing were perfect) | 62.26% | both |
| Classes | 428 sub-industries (avg 3 per MSTAR, range 1–13) | docx |
| **NEW (score TBD):** SecBERT transformer | 407 classes, 3- & 5-epoch; **macro F1 not yet computed** | `Task 2 updated+/` |

> ⚠️ The new SecBERT Task 2 artifacts (`Task 2 updated+/`) contain only model weights + checkpoints and log **`eval_loss` only (1.99 at epoch 3) — no macro-F1/accuracy was computed.** Until inference is run, the only defensible Task 2 number is the **Hybrid Cascade 55.4%**. (You're computing the SecBERT score separately.)

### BreezeML
- `pip install breezeml`, authored by Akash A.G., **5 releases (v0.2.1 → v0.2.5)**
- v0.2.3 primal SVM fix: training 20+ min → <2 sec
- v0.2.5 balanced class weights → eliminated SMOTE

---

## 2. Slide-by-slide findings

### Slide 1 — Title
- **P3** Inconsistent casing/spacing: *"Can a Machine Read a company and know its Industry ?"* → recommend *"Can a Machine Read a Company and Know Its Industry?"* (capitalize "Company", drop the space before "?").
- **P3** *"Group 4 MGT 599 –Capstone"* — stray en-dash with odd spacing. Use *"Group 4 · MGT 599 Capstone"*.
- ✅ "DePaul University" is correct. (An old draft, `PRESENTATION_CONTENT.md`, said "Strayer University" — do **not** reintroduce that.)

### Slide 2 — Agenda
- **P2** *"Twelve minutes."* — your delivery target is ~10 min (Week 7 report: "runtime hit 10 minutes target"). Either say "ten minutes" or genuinely plan for 12. Pick one and rehearse to it.
- ✅ 23,207 companies / 145 industries — consistent.
- **Note:** agenda lists 5 chapters; Task 2 isn't one of them → it lives inside the demo + verbal close.

### Slide 3 — Problems & Stakes
- **P1 — REAL CONFLICT.** The phone graphic reads **"COMPANIES 17,432 from our dataset."** Every other slide (2, 5) and all reports say **23,207** companies / 53,585 records. Decide which is right and make it consistent. If 17,432 is a real subset (e.g. companies after a filter), label it as such; otherwise change it to 23,207.
- **P3** Double space in *"doesn't  survive new IPOs"*.
- ✅ 35.1% multi-segment, 55.2% ambiguity, 53,585 records — all consistent with sources.

### Slide 4 — Research (RQ1–3)
- ✅ Reads cleanly. RQ2 "hierarchical (sector → group → industry) vs flat 145-class" matches the architecture. RQ3 "structural ceiling" matches the ~76% ceiling analysis. No number issues.

### Slide 5 — Data Foundation
- ✅ "23,207 companies. 53,585 records. Ten columns." — consistent.
- ✅ SPLIT "42,116 train · 10,535 test" matches the company-disjoint joined counts (Week 6 report: 42,116/42,868 train, 10,535/10,717 test). Good.

### Slide 6 — BreezeML / Models
- **P2 — Version inconsistency.** Header says **"Latest Release V3.1.0"**, the terminal mockup says **"breezeml-0.2.4"**, and slide 10 says **"v0.2.1 → v0.2.5"**. Reconcile: *V3.1.0* appears to be the TAVSS engine/model version, while **breezeml's latest is v0.2.5** (not 0.2.4). Align the pip line to `breezeml-0.2.5` and make clear V3.1.0 ≠ the library version.

### Slide 7 — The Mirage (leakage audit)
- ✅ 88.9% leaked, 97.2% test rows seen in training — matches `CASCADE_AUDIT.md`. This is the strongest slide; keep it.
- **P3** Bottom caption ends a touch abruptly ("…We rebuilt."). Fine as a punch; just confirm it isn't visually clipped on the presentation machine.

### Slide 8 — Classification Engine / progression montage
- **P2** This slide mixes **70.29** (single-model dev F1) and **75.0%** (final ensemble) in the same montage. Not wrong, but a panelist could read 70.29 as "the result." The speaker must frame it as *progression → final*: "single model 70.29 dev, final calibrated ensemble 75.0." (Handled in the script.)
- ✅ "Company-disjoint" badge, 91.4%, 59.65% all check out.

### Slide 9 — Honest Verdict (terminal log)
- **P1 — Likely typo: `recommend_to_rod_team`.** The client is the **RED** team (Reference Entity Data). Almost certainly should be `recommend_to_red_team`. A Morningstar panelist will notice. Fix.
- **P2 — `pypii_releases` looks like a typo** (double "i"). Should be `pypi_releases`. Verify on the slide and fix.
- ✅ `macro_f1 :: 0.750`, `top_3_accuracy :: 0.914`, `Morningstar ≥ 0.75` — all consistent and on-message (you cleared the bar).
- **P3** `hours_invested :: 258+` and `obstacles_navigated :: 14` are narrative flourishes, not from a source file. Fine for tone, but be ready to not over-defend them if asked.

### Slide 10 — What We Built / Learned (75% recap)
- ✅ 75.0% (4-model ensemble, calibrated), 91.4% top-3, breezeml "5 releases v0.2.1 → v0.2.5", HIERARCHY FIRST pyramid — all consistent.
- **P1** **Task 2 is absent here.** This is the natural place to acknowledge it verbally (the script puts Task 2 in this speaker's segment). Consider a one-line "Task 2: 428 sub-industries, hybrid cascade 55%" or a backup slide.

### Slide 11 — TAVSS Engine Demo
- ✅ Team names confirmed: **Tserennadmid · Akash · Vishal · Subasree · Srilaxmi** (5 presenters). Use these exact spellings everywhere (the older `TALKING_SCRIPT.md` spelled the first name "Toremohmd" and listed only 4 people — outdated).
- **P2** Have a **backup screenshot/video** of the live demo in case the laptop/network misbehaves. Pre-load the demo in a browser tab before you start.

---

## 3. Rubric coverage (out of 100)

| Rubric area | Covered? | Notes |
|---|---|---|
| Attention-getting opener + purpose | ✅ | Slide 1 hook + RQs |
| Outline + **division of labor** | ⚠️ | Agenda exists; **division of labor across the 5 speakers is not shown on a slide.** The rubric explicitly asks for it — say it out loud on the agenda/intro (script does this) or add it to slide 2. |
| Focuses on critical issues | ✅ | Leakage audit, structural ceiling |
| Relevant quantitative data | ✅ | Strong throughout |
| Detailed illustrations/examples | ✅ | BreezeML, mirage donut, GECS engine |
| Main points reviewed | ✅ | Slide 10 |
| Well-connected flow / ending | ✅ | Verdict → demo → close |
| **No info overload / legible / error-free** | ⚠️ | Fix the typos (slide 9), the 17,432/23,207 conflict, and version mismatch to protect the /20 "error-free" criterion. |

**Biggest free points available:** put the **division of labor** somewhere explicit, and clear the small **errors** (rubric rewards "free from errors").

---

## 4. Q&A landmines to prepare for

1. **"Did you meet the success criteria?"** — Macro F1 ≥ 0.75: **yes, 75.0%.** Top-10 F1 > 0.85: **not clearly met** — be honest, frame as in-progress and tied to the conglomerate ceiling.
2. **"Your number went 88.9 → 75 — did you regress?"** — No: 88.9 was leakage (97.2% seen in training); 75.0 is honest on company-disjoint splits.
3. **"What about Task 2?"** — Hybrid cascade 55.4% macro F1, +19pp over DeBERTa, oracle ceiling 62.3%; SecBERT transformer being finalized. (Don't quote a SecBERT number until computed.)
4. **"Is 75% calibrated number overfit?"** — Disclose: uncalibrated 73.95%, CV 73.96%, test-tuned upper bound 77.51%; headline is the calibration-method result with full disclosure.
5. **Avoid the old marketing claim** "Beats fine-tuned DeBERTa by +24.9pp" (from `TAVSS_Project_Overview.docx`) — that used the **leaked 88.9%** and is no longer defensible.

---

## 5. Fix list (copy/paste checklist)

- [ ] **P1** Slide 3: reconcile **17,432 vs 23,207** companies
- [ ] **P1** Slide 9: `rod_team` → `red_team`
- [ ] **P1** Prepare Task 2 verbally (script ready) + optional one-liner on slide 10
- [ ] **P1** Be ready for the top-10 F1 > 0.85 criterion question
- [ ] **P2** Slide 6: `breezeml-0.2.4` → `breezeml-0.2.5`; clarify V3.1.0 = engine, not library
- [ ] **P2** Slide 9: `pypii_releases` → `pypi_releases`
- [ ] **P2** Slide 2: "Twelve minutes" → match real target (~10)
- [ ] **P2** Add/say the 5-way division of labor (rubric ask)
- [ ] **P2** Backup demo screenshot/video loaded
- [ ] **P3** Slide 1 title casing + en-dash; slide 3 double space
- [ ] Compute the SecBERT Task 2 macro-F1 (separately) and drop it into the script placeholder
