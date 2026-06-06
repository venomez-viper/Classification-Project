# GECS-Sage — Handoff Playbook to Next LLM Assistant

**Project:** MGT 599 Capstone · Morningstar GECS Industry/Subindustry Classification
**Owner:** Akash Anipakalu Giridhar (lead) · Group 4 · DePaul University Chicago
**Audience for final presentation:** Morningstar Reference Entity Data (RED) team — they are coming to class
**Submission deadline:** Monday, May 18, 2026
**Document date:** May 11, 2026 (T-minus 7 days)
**Status:** Do-or-die week. All major decisions locked. Execution mode.

> This document is the complete handoff. Any LLM assistant (GPT-5, Gemini, Claude Haiku, etc.) reading this should be able to continue the project without re-deriving anything. Read sections 1–4 first. Then jump to section 7 for "what to do right now."

---

## 1. Context — what this project actually is

**The case.** Morningstar's RED team owns the Global Equity Classification Standard (GECS) — a 4-level hierarchy that maps every public company to a sector → industry group → industry → business activity. They want to know if ML can scale this work.

**The data, case-issued:**
- `task1_gecs_classification_final.csv` — 53,585 rows, 145 industry codes (Task 1)
- `task2_subindustry_classification_final.csv` — 27,537 rows, 450 business activity codes (Task 2)
- We have cleaned versions: `data/cleaned/task1_clean.csv`, `data/cleaned/task2_clean.csv`
- Train/test split provided: `llm_finetuning/data/task1_train.csv` (42,868) and `task1_test.csv` (10,717)

**Case success criteria (stated):**
- Macro F1 ≥ 0.75 overall
- F1 > 0.85 for top-10 most-frequent classes

**Our brutally honest position:**
- Best honest result so far: **V10 calibrated stack — 69.09% Macro F1, 2/10 top-10** *(V10's joblib was never saved; must be reproduced tonight, otherwise V13 at 67.99% is the locked production baseline — see Section 2)*
- Realistic landing zone after Week 5 work: **74–77% Macro F1, 5–7/10 top-10**
- 10/10 top-10 is not survivable in 7 days. The Diversified Industrials class (`31030010`) caps at ~35% F1 across all our experiments; it is structurally ambiguous (conglomerates).

**The differentiation story (what wins Morningstar's respect):**
1. We caught a 30-percentage-point data leakage in our own Week 3 baseline (88.90% → honest 60%). Most teams won't catch theirs.
2. We parsed the Morningstar 2019 GECS PDF and use the 145 official industry definitions as semantic anchors. Nobody else does this.
3. We're building a deployable analyst-in-the-loop product, not a notebook with one F1 number.
4. The number we deliver will be real. Documented end-to-end.

---

## 2. What's already built (treat as locked assets)

### Saved models / artifacts

**⚠ READ THIS FIRST.** The actual current best **deployable** artifact is V13 (67.99%), NOT V10. V10's joblib was never saved. Treat V10 as a "reproduce-if-possible" target tonight; treat V13 as the locked production baseline if V10 cannot be reproduced cleanly. Both numbers are submission-worthy when paired with the audit story.

| Path | What it is | F1 | Deployable now? |
|---|---|---|---|
| `models_v13/v13_linearsvc_c1.joblib` | TF-IDF + MiniLM + BGE + GECS PDF anchors + class prototypes (123k features) | **67.99%** | ✅ **YES — this is the real fallback** |
| `models_v6/v6_flat_svm.joblib` + vectorizers + scaler | TF-IDF + BGE-base hybrid, full bundle | 67.70% | ✅ Yes |
| `models_v14/training_summary.json` (no joblib) | RAC: KNN over training + KNN over GECS taxonomy | 66.04% | ❌ No artifact saved |
| `models_v10/` (EMPTY) | Calibrated stack — claimed 69.09% but never saved | 69.09% (claimed) | ❌ Must reproduce tonight |
| `embeddings_v4/` | MiniLM cached embeddings for train + test + 145 anchors | — |
| `embeddings_v6_bge/` | BGE-base cached embeddings for train + test + 145 anchors | — |
| `gecs_taxonomy.json` | All 145 official GECS industry definitions parsed from PDF | — |
| `server_legendary.py` (126 lines, Flask) | Existing API with routing, CORS, taxonomy crosswalk, explanation generator. **PATCH, DO NOT REWRITE.** | — |
| `frontend/` (Next.js 13 app router) | Existing UI, needs new pages | — |

### Documents already written
- `docs/Initial_Proposal_TAVSS.docx` — formal initial proposal, McKinsey-style, 9 sections + 4 appendices, all 10 case-alignment patches applied
- `docs/Initial_Proposal_McKinsey.docx` — identical content, alternate filename
- `docs/Week5_Report.docx` — Week 5 progress report following Week 3/4 format
- `docs/Week5_Team_Tasks.docx` + `.md` — per-member task sheet (Srilaxmi, Vishal, Subasree, Tserennad)
- `docs/LEGENDARY_PLAYBOOK.docx` + `.md` — internal strategy for the Monday presentation
- `CASCADE_AUDIT.md` — the leakage audit document (your single strongest deliverable)
- `PROJECT_JOURNEY.md` — week-by-week narrative
- `CODEX_BUILD_TASKS.md` — task list for Codex to handle deployment infra
- `docs/proposal_exhibits/*.png` — 6 publication-quality chart exhibits

---

## 3. The locked decisions (do not relitigate)

### Killed and not coming back
- ❌ DeBERTa-v3-base fine-tuning. Three failed runs. Not retrying.
- ❌ FinBERT. Domain mismatch (financial news ≠ company descriptions). 61.84% F1.
- ❌ V11 gte-large encoding. 30+ hour encoding time on Colab. Killed.
- ❌ V9 manual contrastive fine-tune. Collapsed the embedding space.
- ❌ Full FastAPI rewrite of the server. Existing `server_legendary.py` is patchable.
- ❌ Distillation via the paid Claude API. We are not paying.
- ❌ 10/10 top-10 pass target. Not survivable in 7 days. Aim for 6–8/10.

### Locked in (do these, in this order)
- ✅ Primary encoder upgrade: **`answerdotai/ModernBERT-base`** (149M params, drop-in BERT replacement, beats DeBERTa-v3-base on GLUE 88.4 vs 88.1, designed for FP16/bf16 stability with FlashAttention-2 + pre-norm)
- ✅ Domain backup: **`pborchert/BusinessBERT`** (BERT-base pretrained on company websites + 10-K MD&A, +3-4 F1 on business classification tasks)
- ✅ Multi-task heads: Sector (11) + Group (55) + Industry (145), joint loss α=0.2, β=0.3, γ=0.5
- ✅ Long-tail loss: Distribution-Balanced (DB) loss on the industry head
- ✅ Mixed precision: **bf16**, not fp16 (bf16's 8-bit exponent avoids the gradient underflow that broke DeBERTa)
- ✅ Optimizer: StableAdamW (or AdamW with conservative LR)
- ✅ Conglomerate binary branch: a small classifier on segment_count + revenue_share_std that routes ambiguous predictions to `31030010` with elevated recall
- ✅ Distillation reasoning chains: **Qwen2.5-32B-Instruct via vLLM on Colab A100** generates reasoning chains over GECS PDF definitions — used as soft labels and demo reasoning traces, not as the primary classifier
- ✅ Demo LLM judge: **Qwen2.5-3B-Instruct via Ollama on Akash's laptop** — fires for low-confidence predictions
- ✅ Deployment: **Hugging Face Spaces (Gradio)** primary, laptop demo as backup
- ✅ Existing server patch over rewrite

### Quantitative budget
- Colab Pro+ compute units available: ~600 (4% used so far)
- Total Colab GPU-hours to spend: ~20–25 across all of this week
- Training time budget per single run: 6 hours (Colab session safety)

---

## 4. The 7-day execution plan

```
Calendar reference: 7 days from "today" (T+0) to submission (T+7).
Verify the actual calendar dates on your laptop before scheduling team meetings.

T+0 — TONIGHT  (CPU only, no compute)
├── A. Try to reproduce V10 calibrated stack from scripts/ — SAVE joblib
│       If V10 reproduction fails → V13 (67.99%) is the locked baseline. Move on.
├── B. Build scripts/build_task2_classifier.py with Task 1 → Task 2 hard constraint
│       FIRST: verify the deterministic one-to-many mapping holds in the actual data
│       (for every CompanyId+AsOfDate, does each subindustry roll up to exactly one industry?)
├── C. Patch server_legendary.py: replace softmax-on-margin with CalibratedClassifierCV proba.
│       Run the existing server first to catch import errors before adding endpoints.
├── D. Set up Colab notebook scaffolding for ModernBERT-base fine-tune
├── E. Hand CODEX_BUILD_TASKS.md + FULL_SYSTEM_REVAMP.md to Codex
│       Tell Codex: read existing files first. Don't delete the existing frontend pages.

T+1 — Big training day on Colab
├── 09:00  SMOKE TEST: ModernBERT-base, 500 samples, 1 epoch on A100-40GB
│         Budget 60 minutes (model download + load + run, not 30).
│         If still healthy at 60 min with decreasing loss → continue.
│         If it crashes hard → switch to BusinessBERT smoke (different recipe — see below).
│         If smoke survives at F1 ≥ 65% on dev subset → full training kicks
├── 10:30  FULL TRAINING: 3 epochs, segment-only input, multi-task heads
│         bf16, batch 16, StableAdamW, DB loss on industry head
│         Estimated 4 hours on A100
├── During training: CPU work in parallel:
│         - Build conglomerate binary branch (segment_count + share_std features)
│         - Per-class threshold tuning on V13 (target: push top-10 from 2 to 4-5/10)
│         - Wire Task 2 into the patched server
├── 15:00  Eval ModernBERT on test set. Record numbers.
├── 16:00  GATE 1: If ModernBERT F1 ≥ 70%, kick distillation Step 1
│         Qwen2.5-32B-Instruct via vLLM labels ~3000 reasoning chains
│         (~6 hours unattended — finishes by midnight)
└── 23:00  Check teacher output quality on 100 samples.
         If teacher-vs-truth agreement < 75%, abort distillation.

T+2 — Ensemble + lock
├── 09:00  Distillation chains done (if launched)
├── 09:30  Build meta-classifier ensembling: ModernBERT logits + V13 probs + 
│         RAC features + GECS anchor sims → calibrated combined head
├── During: Codex completes HF Space scaffold + Gradio UI
├── During: hierarchical-aware top-10 threshold tuning
├── 18:00  HARD GATE: lock the model. No more training after this.

T+3 — Deploy
├── Bundle final artifacts (model.onnx or model.pt + vectorizers + taxonomy + neighbor index)
├── Push to Hugging Face Space
├── Verify live URL works from a phone
├── Latency benchmarks: target p95 < 500ms on HF CPU
├── End-to-end smoke test: 20 hand-picked test examples
└── Update CASCADE_AUDIT.md and PROJECT_JOURNEY.md with final numbers

T+4 — Writeup
├── Confusion matrix per top-10 class
├── Final Report consolidating Initial Proposal + Week 5 + final results
└── Start presentation slides (12 slides)

T+5 — Practice
├── Slide finalization
├── Dry run with the team
└── Test BOTH HF Space URL and laptop demo (backup) at the rehearsal

T+6 — Buffer day

T+7 — Submit + present
├── Morning: test HF Space URL again. Test laptop demo again.
├── Push everything to GitHub before walking in.
└── Walk in with the URL ready on your phone.
```

### BusinessBERT fallback recipe (if ModernBERT smoke crashes)

If `answerdotai/ModernBERT-base` cannot be loaded or trained on Colab, switch to `pborchert/BusinessBERT` with **different hyperparameters** (it's BERT-base, not ModernBERT — recipe differs):

```
model_name        = 'pborchert/BusinessBERT'
max_seq_length    = 512                # NOT 8192 — BERT-base only supports 512
batch_size        = 16
gradient_accum    = 4
mixed_precision   = 'bf16'             # still bf16, not fp16
optimizer         = 'AdamW'            # standard AdamW, not StableAdamW
encoder_lr        = 2e-5               # standard BERT rate, NOT 1e-5
head_lr           = 2e-4               # standard head rate
warmup_ratio      = 0.1                # 10%, not 5%
epochs            = 3
no FlashAttention                       # BusinessBERT doesn't support it natively
no gradient_checkpointing               # avoid the FP16 grad path entirely
```

---

## 5. What "stellar" looks like to Morningstar — the legendary positioning

> **"Industry classification is not 100% automatable. The right product is an analyst-first system where the model handles the obvious cases, defers on hard ones, and explains every decision using the company's own taxonomy."**

Say that sentence twice in the presentation. Once at minute 1, once at minute 30.

### Three-act narrative for the pitch
- **Act I (Weeks 1–3):** "We built a TF-IDF cascade and got 88.90% Macro F1. We almost shipped it."
- **Act II (Week 4):** "We audited our own evaluation pipeline. 97.2% of our test set was in training. The 88.90% was leaked memorization. The honest number was 60%."
- **Act III (Weeks 5–7):** "We rebuilt everything. Here's the live demo at [HF Space URL]."

### Five legendary moves to ship this week
1. **Lead with the audit** (Move 1 slide). Don't bury it.
2. **Cite the exact GECS PDF phrase** that matched in every prediction. Demonstrates domain humility.
3. **Build an Override button.** The system surfaces top-3, the analyst is final authority.
4. **Deploy live on Hugging Face Spaces.** A URL Morningstar can hit from their phone.
5. **Name what we cannot solve** (class 31030010) and recommend the analyst-review workflow around it.

### The closing line (verbatim, after Q&A)
> *"We didn't try to replace your analysts. We tried to build the tool we'd want as one of them. Everything in this system is grounded in your taxonomy, calibrated honestly, and deployable on infrastructure you already have. We'd love to hear what would need to change for this to land in RED's workflow."*

This flips the energy in the room from "graded student" to "hiring conversation."

---

## 6. The technical architecture — what we're actually shipping

```
                    HUGGING FACE SPACE (free tier, Gradio UI)
        ┌──────────────────────────────────────────────────────────┐
        │  User pastes company segment description                 │
        └────────────────────────┬─────────────────────────────────┘
                                 ▼
        ┌──────────────────────────────────────────────────────────┐
        │  Multi-encoder retrieval (cached + frozen)               │
        │  ── TF-IDF segment + LongProfile (120k features)         │
        │  ── MiniLM-L6 embeddings (384d)                          │
        │  ── BGE-base embeddings (768d)                           │
        │  ── Cosine sim to 145 GECS PDF anchors (per encoder)     │
        │  ── KNN over training corpus (RAC, top-25 neighbors)     │
        │  ── Numerical features (5: revenue_share, etc.)          │
        └────────────────────────┬─────────────────────────────────┘
                                 ▼
        ┌──────────────────────────────────────────────────────────┐
        │  ModernBERT-base classifier (fine-tuned, ONNX, INT8)     │
        │  ── Sector head (11 classes)                             │
        │  ── Group head (55 classes)                              │
        │  ── Industry head (145 classes)                          │
        │  ── Conglomerate binary branch (revenue dispersion)      │
        └────────────────────────┬─────────────────────────────────┘
                                 ▼
        ┌──────────────────────────────────────────────────────────┐
        │  Meta-classifier (BreezeML-trained calibrated head)      │
        │  ── Combines all signals into final top-3 + probabilities│
        │  ── Per-class threshold tuning                           │
        │  ── Hierarchical Task 1 → Task 2 constraint              │
        └────────────────────────┬─────────────────────────────────┘
                                 ▼
        ┌──────────────────────────────────────────────────────────┐
        │  Optional LLM judge (Qwen2.5-3B via Ollama)              │
        │  Fires when top-1 confidence < 0.7                       │
        │  Returns: chosen code + reasoning trace                  │
        └────────────────────────┬─────────────────────────────────┘
                                 ▼
        ┌──────────────────────────────────────────────────────────┐
        │  Display: top-3 + GECS definition quote + reasoning +    │
        │  processing trace + [Accept] [Override] [Flag] buttons   │
        └──────────────────────────────────────────────────────────┘
```

Target p95 latency on HF Spaces CPU: **< 500ms** (with INT8-quantized ModernBERT).

---

## 7. WHAT TO DO RIGHT NOW (Sunday night, May 11)

In this order. No compute spend. ~4-5 hours of CPU work.

1. **Try to reproduce V10 and save the joblib.**
   - Run the existing V10 training script (search for it in `scripts/` — it's the one that produced the V10 calibrated stack, likely named `train_cascade_v10_calibrated.py`)
   - Save: `models_v10/v10_calibrated.joblib`, `models_v10/v10_vec_seg.pkl`, `models_v10/v10_vec_long.pkl`, `models_v10/v10_scaler.pkl`
   - Verify F1 ≈ 69.09% on `task1_test.csv` (within 1pp tolerance)
   - **If V10 reproduction fails for any reason** (script broken, sklearn version mismatch, etc.): stop after 30 minutes. V13 (`models_v13/v13_linearsvc_c1.joblib` at 67.99%) is the locked production baseline. Update all downstream docs (slides, README, Final Report) to cite 67.99% instead. Move on.
   - Either way, you have an insurance baseline — if T+1's ModernBERT training collapses, you still ship 67–69%.

2. **Build Task 2 classifier with hierarchical constraint.**
   - **STEP 1 (5 minutes):** Verify the Task 1 → Task 2 deterministic mapping. Load `data/cleaned/task1_clean.csv` and `data/cleaned/task2_clean.csv`. Join on (CompanyId, AsOfDate). For each subindustry code, check that it ALWAYS rolls up to the same industry code. If any subindustry maps to multiple industries, document those exceptions and decide how to handle them (probably: majority vote per subindustry, document as a known limitation).
   - **STEP 2:** Load `data/cleaned/task2_clean.csv`
   - **STEP 3:** Train a Linear SVM with class_weight='balanced' on segment text only
   - **STEP 4:** At inference: predict Task 1 first, then restrict Task 2 candidates to that industry's children (with the exceptions handled per step 1)
   - **Save:** `models_task2/task2_classifier.joblib` and `models_task2/task1_to_task2_map.json` (the verified mapping)
   - **If the mapping has > 5% violations:** drop the hard constraint, use the predicted Task 1 as a soft prior instead. Document the limitation in the final report.

3. **Patch `server_legendary.py`.**
   - Replace `softmax(decision_function_margin)` with `CalibratedClassifierCV.predict_proba`
   - Add a `/predict` endpoint that returns Task 1 + Task 2 + top-3 + GECS definition lookup
   - Add SQLite logging of every prediction
   - Do NOT rewrite the file. Patch in place.

4. **Prepare the Colab notebook for Monday morning.**
   - `colab/modernbert_finetune.ipynb`
   - Cells: setup → upload data → tokenize → build MultiTaskHTC class → DB loss → training loop with bf16 → save weights to Drive
   - Use `answerdotai/ModernBERT-base` as the backbone
   - 3 heads: sector_head (11), group_head (55), industry_head (145)
   - Use SegmentName + SegmentDescription only (no LongProfile — that was the contamination source)

5. **Hand off Codex tasks.**
   - Give Codex the `CODEX_BUILD_TASKS.md` file MINUS the FastAPI rewrite section (we're patching, not rewriting)
   - Codex builds: HF Space Gradio app, frontend pages, architecture diagram, deployment runbook, slides, README polish

---

## 8. Monday 9 AM — the Colab execution plan

1. **Open Colab Pro+, confirm A100 GPU** (`!nvidia-smi`). If not A100, disconnect and reconnect until you get one.
2. **Mount Google Drive** (`drive.mount('/content/drive')`).
3. **Upload `task1_train.csv`, `task1_test.csv`, and `gecs_taxonomy.json`.**
4. **Run smoke test cell first:** 500 samples, 1 epoch, watch for OOM or NaN loss. If clean, proceed.
5. **Run full training:** 3 epochs, batch 16, bf16, StableAdamW, DB loss. Estimated 4 hours.
6. **Save model state to Drive every epoch.** Sessions die unpredictably.
7. **At 4-hour mark:** evaluate on test set. Record Macro F1, per-class F1 for top-10, confusion matrix on `31030010`.
8. **If F1 ≥ 70%:** kick off distillation Step 1 (Qwen2.5-32B-Instruct via vLLM, 4-bit, labels ~3000 reasoning chains in ~6 hours — should be done by midnight).
9. **If F1 < 70%:** abort ModernBERT, smoke-test BusinessBERT, or fall back entirely to V10/V13 (whichever you successfully saved last night) + the ensemble + per-class tuning path.

### Key Colab parameters to remember
```
model_name        = 'answerdotai/ModernBERT-base'
max_seq_length    = 512
batch_size        = 16
gradient_accum    = 4
mixed_precision   = 'bf16'    # NOT fp16
optimizer         = 'StableAdamW'
encoder_lr        = 1e-5
head_lr           = 5e-4
warmup_ratio      = 0.05
epochs            = 3
loss              = α·CE(sector) + β·CE(group) + γ·CE(industry)
                    with α=0.2, β=0.3, γ=0.5
                    Distribution-Balanced reweighting on industry head
```

### What to do if the FP16 / unscale error appears again
- We are using **bf16**, not fp16. The unscale error should not happen.
- If it does anyway: remove `gradient_checkpointing_enable()` entirely. Shrink batch to 8 if OOM. Do not call private `_unscale_grads_` methods.

---

## 9. Codex parallel work (give Codex this list, not the FastAPI rewrite)

Codex builds the deployment shell while we build the ML core. The original `CODEX_BUILD_TASKS.md` had 7 tasks; **drop Task 1 (FastAPI rewrite)**. Use the others:

- **Task 2:** Ollama LLM judge module (`serve/llm_judge.py`) — Qwen2.5-3B with timeout fallback
- **Task 3:** Frontend updates — live demo now has top-3 panel, model evidence, processing trace, and Accept / Override / Flag controls wired to `/feedback`
- **Task 4:** Architecture diagram (`docs/architecture/system_diagram.py` → PNG)
- **Task 5:** Deployment runbook (`docs/DEPLOYMENT_RUNBOOK.md`)
- **Task 6:** Slides (`docs/presentation/build_slides.py` → PPTX)
- **Task 7:** README polish

Codex prompt for each task is in `CODEX_BUILD_TASKS.md`. Copy-paste verbatim.

---

## 10. Deliverables checklist for Monday May 18

| Deliverable | Status | Owner |
|---|---|---|
| `docs/Initial_Proposal_TAVSS.docx` | ✅ Done | Akash |
| `docs/Week5_Report.docx` | ✅ Done | Akash |
| `docs/Week5_Team_Tasks.docx` (with team's numbers filled in) | Waiting on team | Team + Akash |
| `CASCADE_AUDIT.md` (updated with Week 5 results) | ⏳ Update Wed | Akash |
| `PROJECT_JOURNEY.md` (updated with final results) | ⏳ Update Wed | Akash |
| Working live Hugging Face Space URL | ⏳ Deploy Wed | Akash + Codex |
| Final Report (consolidates everything) | ⏳ Write Thu | Akash |
| Presentation slides (PPTX, 12 slides) | ⏳ Write Thu | Codex builds skeleton, Akash polishes |
| Trained model artifacts (joblib + onnx) | ⏳ Lock Tue | Akash |
| Task 2 classifier with hierarchical constraint | ⏳ Build tonight | Akash |
| `models_v10/v10_calibrated.joblib` (insurance baseline) | ⏳ Build tonight | Akash |
| Public GitHub repo with weekly commits | ⏳ Final push Sat | Akash |

---

## 11. Hard do-not-do list

- ❌ Do NOT spend more than 30 min on the Monday smoke test before committing to full training
- ❌ Do NOT chase a higher F1 number after Tuesday 22:00. Lock the model.
- ❌ Do NOT use fp16 on Colab. Use bf16. (8-bit exponent vs 5-bit — avoids gradient underflow.)
- ❌ Do NOT use both `WeightedRandomSampler` AND `class_weight='balanced'` together. Pick one.
- ❌ Do NOT use focal loss with gamma=2 on a resumed checkpoint. It will collapse the model.
- ❌ Do NOT enable `gradient_checkpointing` with the legacy `use_reentrant=True`.
- ❌ Do NOT re-run failed experiments hoping they work this time. Move on.
- ❌ Do NOT present a leaked F1 number. The audit IS your story.
- ❌ Do NOT pretend 10/10 top-10 is achievable. Be honest about the conglomerate class.
- ❌ Do NOT rewrite `server_legendary.py`. Patch it.
- ❌ Do NOT claim V10's 69.09% in the final report unless `models_v10/v10_calibrated.joblib` actually exists and loads cleanly. If V10 reproduction failed tonight, **V13 at 67.99% is the production number** — update slides, README, and the Final Report accordingly. Honest 67.99% > a number you can't reproduce.
- ❌ Do NOT walk into the presentation without both the live HF Space URL AND a working laptop demo. Test both Monday morning. If HF Space is down at presentation time, switch to localhost — the prof shouldn't see you scramble.
- ❌ Do NOT enable Ollama in the Hugging Face Space app. HF free tier cannot run it. The HF Space gracefully shows "reasoning trace available in local deploy." Ollama is laptop-only.

---

## 12. Useful prompts ready to paste into other LLMs

### Prompt A — "Continue this project from here" (paste to GPT-5/Gemini/Haiku)

```
You are picking up a graduate ML capstone project at T-minus 7 days from submission. 
Read the attached HANDOFF_PLAYBOOK.md in full before responding. All major decisions 
are locked. Your job is to help execute them, not relitigate them.

Today is [INSERT DATE]. The submission deadline is Monday May 18, 2026. Morningstar's 
Reference Entity Data team is coming to the final presentation.

What I need from you right now: [INSERT SPECIFIC REQUEST — e.g., "help me debug the 
ModernBERT fine-tune that crashed in cell 5", or "write the Task 2 classifier script"]

Constraints you must honor:
- bf16 only, no fp16
- ModernBERT-base is the locked backbone
- Patch server_legendary.py, do not rewrite
- No new model architectures after Tuesday 22:00
- Honest numbers only — the audit story is our differentiation, not inflated F1
```

### Prompt B — "Debug a training failure" (paste to Claude Sonnet/GPT-5)

```
I am fine-tuning ModernBERT-base on a 145-class hierarchical classification task. 
Backbone: answerdotai/ModernBERT-base. Mixed precision: bf16. Optimizer: StableAdamW.
Batch size 16, gradient accumulation 4, learning rate 1e-5 encoder / 5e-4 heads.
Multi-task heads: sector(11), group(55), industry(145). Loss: weighted CE + DB reweighting.

Here's the error:
[INSERT STACK TRACE]

Diagnose the root cause and give me the minimal surgical fix. Do not rewrite the whole 
training loop. Do not suggest switching models. ModernBERT is locked.
```

### Prompt C — "Help me write a section of the final report"

```
You are helping me write the final report for a Morningstar capstone. The audience is the 
RED team and a senior ML engineer. Tone: precise, honest, enterprise-mature. No marketing 
fluff. No emojis.

I need: [INSERT SECTION — e.g., "the methodology section explaining how we caught the 
30-percentage-point data leakage"]

Constraints:
- Lead with the audit as a feature of our work, not a footnote
- Use specific numbers when citing results (e.g., "97.2% test/train overlap")
- Quote the official GECS PDF where relevant
- Keep paragraphs short
```

---

## 13. If everything goes wrong — the graceful fallback

If by Tuesday 22:00 nothing has worked, you still have a strong submission:

1. **V10 calibrated stack at 69.09%** with the GECS-anchor reasoning trace = a real deliverable
2. **The leakage audit** alone is methodology gold worth its own grade
3. **The Initial Proposal already submitted** stands on its own
4. **The Hugging Face Space deploy** with V10 + GECS anchors + Task 2 hierarchical constraint is a real production system
5. **The Legendary Playbook story arc** works at 69% F1 just as well as 80%

The audit + the system + the honest narrative = a hireable submission **even if no new model lands**.

---

## 14. Anchor truths to stay calm

Whatever happens this week, these are unchanging:

1. We caught a 30-percentage-point leakage in our own work. Most teams won't.
2. We grounded every prediction in Morningstar's own GECS PDF.
3. We built an analyst-in-the-loop product, not a science experiment.
4. We documented every iteration end-to-end.
5. We chose honest numbers over inflated ones.

If the final number is 72% — that's a great submission. If it's 78% — that's a great submission. The story is the same. The decision-quality is what they're hiring for.

---

*Prepared May 11, 2026 · Submission deadline May 18, 2026 · Do-or-die week*
*Akash Anipakalu Giridhar · Group 4 · DePaul University Chicago · MGT 599*
