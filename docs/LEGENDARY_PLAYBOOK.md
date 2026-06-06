# The Legendary Playbook for Monday

**MGT 599 Capstone · Final Presentation Strategy**
**Group 4 · Lead: Akash Anipakalu Giridhar**
**Audience: Morningstar Reference Entity Data (RED) team**
**Date prepared: May 11, 2026 · For submission: May 18, 2026**

> *Internal strategy document. Not for submission. Use this to drive every decision in the final week.*

---

## The Goal

Walk out of the Monday presentation having made the Morningstar people feel like they should hire the lead. F1 number alone doesn't do that. Senior judgment, production thinking, and domain humility do.

This document is the playbook for getting there.

---

## 1. The Thesis — one sentence Morningstar will remember

> **"Industry classification is not 100% automatable. The right product is an analyst-first system where the model handles the obvious cases, defers on hard ones, and explains every decision using the company's own taxonomy."**

This is your positioning. Honest, enterprise-mature, and the opposite of what 90% of capstone teams will say. They'll sell *"we built AI."* You sell *"we built a tool your analysts will actually use."*

Say this sentence twice — once at minute 1, once at minute 30.

---

## 2. The Narrative Arc — three acts, not "here's what we did"

### Act I — The Discovery (Weeks 1–3)
> *"We built a TF-IDF cascade and got 88.90% Macro F1. We almost shipped it."*

### Act II — The Audit (Week 4)
> *"Then we audited our own evaluation pipeline. We found that 97.2% of our test set was inside our training set. The 88.90% was leaked memorization. The honest number was 60%. We rebuilt everything from scratch."*

### Act III — The System (Weeks 5–7)
> *"With honest evaluation in place, we built a production-ready classification system grounded in your own 2019 GECS taxonomy document. Here's the live demo."*

**This arc is why they hire you.** Every junior data scientist builds models. The senior ones audit their own work and tell unflattering truths. Lead with the audit, not the F1.

---

## 3. What You Are Actually Selling — a product, not a model

A model is a `.joblib` file. A product is:

- An API analysts can call from their existing workflow
- A UI that explains its reasoning in plain English using the GECS definitions Morningstar wrote
- A confidence number that means something (calibrated, not softmax-on-margin)
- An audit trail of every prediction
- A path to retrain when the taxonomy updates
- A cost-per-prediction number you can defend
- A live URL anyone in the room can hit on their phone

If your final 30 seconds is *"here's how it integrates with RED's workflow tomorrow morning,"* you have stopped being a student to them.

---

## 4. The Five Legendary Moves We Make This Week

### Move 1 — Frame the audit as your *first* contribution, not a footnote
The leakage discovery is your single strongest signal of senior judgment. Every other team will downplay theirs (or will not have caught one). **Lead with yours.** Open the presentation with the 88.90% → 60% slide. Make Morningstar sit up.

### Move 2 — Ground every prediction in the regulator's own words
Nobody else will think to parse the Morningstar 2019 GECS PDF and use its 145 official definitions as semantic anchors. We have. When the demo predicts a code, it cites the exact phrase from the official definition that matched.

**This is domain humility.** It says: *"We didn't invent labels. We used yours."*

### Move 3 — Build the analyst-override workflow, not full automation
Most teams pretend their model is "ready for production." Pre-empt the obvious objection — *"What about the hard cases?"* — by designing for it.

Your system shows top-3 candidates with calibrated confidence and an "Override" button. The message: *the analyst is the final authority; the model makes them 5× faster.* That is the right product story for RED.

### Move 4 — Deploy it as a live URL on Hugging Face Spaces
Walk into the room with a URL. Have the Morningstar rep pull out their phone and type a description. The model responds in 200ms with reasoning.

**You stop being a student the moment they can interact with your system from their own device.** That is the moment.

### Move 5 — Name what you cannot solve, and recommend the workflow
The hardest class, `31030010` Diversified Industrials, will not hit 85% F1. Even humans disagree on conglomerate boundaries.

Most teams will hide this. You surface it explicitly:

> *"Class 31030010 is structurally hard. Even humans disagree on conglomerate boundaries. We recommend routing predictions for this class through RED's senior-analyst review queue. Our system flags them automatically based on segment-count and revenue-dispersion features."*

That slide says: *I understand your business. I understand what ML can and cannot do. I built the workflow around the limitation.* Hireable behavior.

---

## 5. The Demo Flow — five minutes that wins the room

| t (min) | What happens |
|---|---|
| 0:00 | Open the live Hugging Face Space URL on the projector. |
| 0:15 | Paste a real description: *"Operates regional retail banks in the Midwest with ~50 branches focused on commercial lending."* |
| 0:45 | Show the response: Task 1 + Task 2 + official GECS definition quoted + top-3 alternatives + processing trace + ~87% calibrated confidence. |
| 1:30 | Click "Show reasoning" → display the chain: *"Segment text mentions retail banking + regional + commercial lending → Sector 103 Financial Services → Group 10320 Banks → Code 10320020 Banks—Regional."* |
| 2:30 | Paste an ambiguous conglomerate description on purpose. Show the system **deferring** with low confidence: *"Confidence below threshold (54%). Recommend analyst review."* This moment shows judgment, not performance. |
| 3:30 | Switch to the `/metrics` page. Latency p95, predictions logged, confidence histogram. *"This is production-ready, not a notebook."* |
| 4:00 | Ask the Morningstar rep to type their own example. Let them play. |
| 4:30 | Close with the closing line (see Section 7). |

---

## 6. What We Do NOT Do This Week

| Don't | Why |
|---|---|
| Oversell the F1 number | If the number is 72%, say 72%. Morningstar will see through inflation. Your audit story makes a real 72% more credible than a fake 85%. |
| Run more experiments after Tuesday | Lock the model Tuesday night. Spend Wednesday–Friday on packaging, not science. Every team underestimates this. |
| Use buzzwords without code behind them | If you say "RAG," show it in the architecture diagram. If you say "calibrated probabilities," point to `CalibratedClassifierCV` in the code. Empty buzzwords get caught in Q&A. |
| Hide failure cases | Walk through three predictions: one easy, one hard but right, one where the system defers. The deferral wins more credibility than the success. |
| Pitch alone | If the team's there, give one slide each. Morningstar evaluates leadership and team coordination. |

---

## 7. The Closing Line — say this verbatim

After the demo, after the questions, look the Morningstar rep in the eye and say:

> *"We didn't try to replace your analysts. We tried to build the tool we'd want as one of them. Everything in this system is grounded in your taxonomy, calibrated honestly, and deployable on infrastructure you already have. We'd love to hear what would need to change for this to land in RED's workflow."*

That last sentence — **asking for feedback on production fit** — flips the energy in the room. You stop being graded. You become a candidate having a conversation with a hiring manager.

---

## 8. What the Lead (Akash) Personally Does Before Monday

1. **Re-read the GECS PDF cover to cover.** When you cite it in the presentation, cite the exact page. Morningstar people will hear it.

2. **Pre-rehearse with two real Morningstar coverage companies.** Pick two public companies you know. Practice classifying them out loud, including the reasoning. Your demo will be 5× sharper.

3. **Practice the leakage-audit slide alone in the mirror.** Get the timing tight: *"We almost shipped 88.90%. Then we caught a 30-point leak. Here's what we learned about audit discipline."* 90 seconds, no notes.

4. **Sleep before Monday.** A clear head delivering a 72% honest number beats a tired one delivering 85%.

---

## 9. What This Buys You by Monday

When you walk in, you have:

- A **live URL** anyone in the room can touch
- A **90-second audit story** that signals senior judgment
- **Reasoning traces** backed by Morningstar's own text
- **Honest performance numbers** with no asterisks
- A **workflow design** that respects analyst authority
- A **closing line** that invites a hiring conversation

That is what gets remembered. Not the F1.

---

## 10. Anchor Truths to Stay Calm Under Pressure

Whatever happens this week, these stay true:

1. We caught a 30-point leakage in our own work. Most teams won't.
2. We built methodology rigor a junior wouldn't have shown.
3. We grounded every prediction in the regulator's own document.
4. We delivered an analyst-friendly product, not a science experiment.
5. The number we deliver is real. The work to get there is documented end-to-end.

If F1 hits 75% on Monday — great. If it hits 72% — also great. The story is the same. The decision-quality is what they're hiring for.

---

*Prepared by Akash Anipakalu Giridhar · MGT 599 Capstone · DePaul University Chicago*
*Last updated: May 11, 2026*
