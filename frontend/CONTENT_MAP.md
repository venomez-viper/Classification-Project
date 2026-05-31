# TAVSS Website Content Map
> Agent instructions: Every editable content block is listed below with its exact file path, variable name, and current values.
> To update the site, edit the values in the specified file at the specified variable. Do NOT change component structure, classNames, or imports - only the string/number content inside the data arrays and JSX text nodes.

---

## SITE-WIDE CONSTANTS

These numbers and strings appear across multiple pages. Update them all consistently.

| Field | Current Value | File(s) to update |
|-------|--------------|-------------------|
| Task 1 F1 score | `81.02%` | `Hero.tsx` STATS, `HowItWorks.tsx` BENCHMARKS + cards, `Journey.tsx` PHASES[04] + final decision, `app/page.tsx` PAGES[model].desc |
| Task 2 F1 score | `55.44%` | `HowItWorks.tsx` Task2 card, `app/hf/page.tsx` header, `hf_space/app.py` T2_BADGE |
| Training segments | `53,587` / `53K+` / `42K+` | `Hero.tsx` STATS, `HowItWorks.tsx` stats row, `Journey.tsx` STATS |
| Team name | `Group 4` | All pages - do global find-replace |
| University | `DePaul University` | Navigation (footer), `about/page.tsx`, `hf_space/app.py` |
| Course | `MGT 599` | All pages - do global find-replace |
| GitHub repo | `https://github.com/venomez-viper/Classification-Project` | `components/Team.tsx` line 194 |

---

## PAGE BY PAGE

### 1. Hero Section
**File:** `frontend/components/Hero.tsx`

#### Badge text (line 68)
```
MGT 599 Capstone . Morningstar RED Team . Group 4
```

#### Hero headline (lines 79-87)
```
GECS
Classification
Engine
```

#### Hero subheadline (lines 96-101)
```
An audited GECS-Sage cascade built on breezeml and Morningstar taxonomy grounding.
Ships a locked V3 Meta-Ensemble (81.02% F1), a constrained Task 2 cascade,
ensuring highly trustworthy results.
```

#### CTA buttons (lines 131-141)
- Primary: `Launch TAVSS App` → href `/login`
- Secondary: `About the Project` → href `/about`

#### STATS array (lines 10-14) - 4 animated counters
```js
{ label: "GECS Industries",    value: 145,   suffix: "" }
{ label: "Sub-Industries",     value: 428,   suffix: "" }
{ label: "Training Segments",  value: 53587, suffix: "+" }
{ label: "Locked Task 1 F1",   value: 81.02, suffix: "%", decimal: true }
```

---

### 2. Home Page
**File:** `frontend/app/page.tsx`

#### PILLARS array (lines 124-140) - 3 cards below hero
```
1. title: "Structured Data Work"
   desc: "The project treats messy company descriptions like a production input stream, not a classroom toy dataset."

2. title: "Model Choices With Consequences"
   desc: "Classical ML and LLM approaches were both tested, but only one earned the production role."

3. title: "Failure-Aware Deployment"
   desc: "The app is now easier to keep useful even when Railway or Hugging Face are unavailable."
```

#### JOURNEY_STOPS array (lines 69-94) - 4 clickable cards
```
01. title: "Frame the business problem"
    desc: "Morningstar descriptions, real class imbalance, and an industry taxonomy too broad for shortcuts."
    href: /about

02. title: "Engineer the text pipeline"
    desc: "Sparse TF-IDF features, vocabulary tuning, and a training path built around control and speed."
    href: /features

03. title: "Audit the model honestly"
    desc: "We caught the leaked Week 3 result, rebuilt the baseline, and made the methodology audit part of the final product story."
    href: /model

04. title: "Deploy and demonstrate"
    desc: "A product flow that can still lean on local services when remote deployments fail."
    href: /demo
```

#### TEAM_HIGHLIGHTS array (lines 96-122) - team spotlight section
```
{ name: "Akash",         role: "ML engineering",    desc: "Inference stack, breezeml architecture, and deployment plumbing." }
{ name: "Subasree",      role: "Evaluation",         desc: "Per-class diagnostics, metrics analysis, and results synthesis." }
{ name: "Vishal",        role: "Feature engineering",desc: "TF-IDF design, sparse vector experiments, and pipeline validation." }
{ name: "Srilaxmi",      role: "Preprocessing",      desc: "Data structure review, cleaning rules, and imbalance constraints." }
{ name: "Tserennadmid",  role: "Documentation",      desc: "Reports, repo coordination, and project continuity across weeks." }
```

#### PAGES array (lines 17-67) - module cards at bottom of home
```
1. href:/ml       title:"TAVSS Control Center"   badge:"MLOps"       color:red
   desc: "A real-time MLOps dashboard monitoring pipeline health, metrics, and model behavior."

2. href:/features  title:"Feature Engineering"   badge:"NLP"         color:red
   desc: "How raw company text became a 60,000-dimensional sparse representation using TF-IDF."

3. href:/breezeml  title:"breezeml Library"       badge:"v0.2.5"      color:blue
   desc: "The PyPI package we built, patched, and used to support the production inference flow."

4. href:/model     title:"Model and Results"      badge:"Audited"     color:cyan
   desc: "GECS-Sage now presents the audited story: The V3 Meta-Ensemble is the locked Task 1 baseline (81.02% F1 Demo State), and Task 2 is fully constrained by the Task 1 parent."

5. href:/graph     title:"Knowledge Graph"        badge:"Interactive" color:emerald
   desc: "An interactive graph connecting companies, segments, subindustries, and keywords."

6. href:/demo      title:"Live Demo"              badge:"Live"        color:amber
   desc: "Paste a company description and watch the classifier assign a Morningstar GECS code in real time."

7. href:/team      title:"The Team"               badge:"Group 4"     color:rose
   desc: "Five MGT 599 students who turned a difficult capstone into a working product."
```

#### Section headlines on home page
- Guided journey section (line 191): `"A clearer path through the capstone"`
- Journey sub-copy (lines 193-196): `"Start with the business problem, move through the engineering tradeoffs..."`
- Team spotlight headline (line 253): `"The people behind the pipeline now sit inside the story"`
- Team spotlight sub-copy (lines 255-258): `"The dedicated team page already existed..."`
- Team right card headline (line 278): `"Five roles. One finished system."`
- Modules section headline (line 316): `"Dive into the modules that make the system real"`
- Footer (line 354): `© 2026 TAVSS | MGT 599 Capstone | Group 4 | DePaul University Chicago`

---

### 3. About Page
**File:** `frontend/app/about/page.tsx`

#### Page headline (lines 59-61)
```
GECS-Sage is built
around the audit.
```

#### Page subheadline (lines 63-65)
```
We started with a flashy cascade result, found leakage, and rebuilt the product around
reproducible baselines, Morningstar taxonomy grounding, and analyst review.
That honesty is the point.
```

#### Stats grid (lines 78-88) - 6 metric cards
```
{ v:"67.99%", l:"Locked Task 1 F1",   s:"V13 deployable baseline",   color:red    }
{ v:"55.44%", l:"Task 2 Macro F1",    s:"428 constrained classes",   color:blue   }
{ v:"88.90%", l:"Audit finding",      s:"leakage, not shipped",       color:amber  }
{ v:"145",    l:"GECS industries",    s:"Task 1 taxonomy",            color:emerald}
{ v:"53K+",   l:"Training segments",  s:"Morningstar company data",   color:violet }
{ v:"Qwen",   l:"Teacher labels",     s:"Colab experiment path",      color:cyan   }
```

#### ARCHITECTURE array (lines 31-35) - 3 architecture cards
```
1. title:"Data to features"     desc:"Company and segment text flows into sparse model features and GECS taxonomy lookups."
2. title:"Audited inference"    desc:"The app does not hide the leakage correction. It separates audit history from deployable performance."
3. title:"Product surface"      desc:"The frontend shows predictions, alternatives, model version, confidence, and review-oriented traces."
```

#### Model decision section
- Left card title: `V13 Task 1 Stack` - score: `67.99%` - label: `Macro F1 · reproducible artifact`
- Left card body: `"The serving path prioritizes the model we can load, explain, and defend..."`
- Right card title: `Leaked Week 3 Run` - score: `88.90%` - label: `Documented, not shipped`
- Right card body: `"This number stays in the project because it proves we audited ourselves..."`

#### STACK array (lines 15-21) - tech stack cards
```
{ label:"Serving API",         value:"Flask + Waitress on localhost:5003, with /predict, /history, /metrics, /feedback" }
{ label:"Frontend",            value:"Next.js 15 + Tailwind CSS, proxying to the GECS-Sage Flask contract" }
{ label:"Task 1 baseline",     value:"V13 locked deployable fallback at 67.99% Macro F1" }
{ label:"Task 2 cascade",      value:"Constrained 428-class sub-industry classifier at 55.44% Macro F1" }
{ label:"Taxonomy data",       value:"Morningstar GECS definitions with GICS, NAICS, and SIC crosswalk support" }
{ label:"Experiment track",    value:"ModernBERT and Qwen notebooks run in Colab Pro+ without becoming unsupported claims" }
```

#### TEAM array (lines 23-29) - team list on about page
```
{ name:"Akash Anipakalu Giridhar",      role:"ML engineering, cascade architecture, deployment" }
{ name:"Subasree Segar",                role:"Model evaluation, benchmarking, per-class diagnostics" }
{ name:"Vishal Shaileshkumar Rathod",   role:"Feature engineering, TF-IDF pipeline" }
{ name:"Srilaxmi Ganjipalli",           role:"Data preprocessing, exploration, cleaning" }
{ name:"Tserennadmid Batkhuu",          role:"Documentation, reporting, project coordination" }
```

---

### 4. Team Page
**File:** `frontend/components/Team.tsx`

#### Page headline (lines 108-111)
```
Five people, five specialties,
one end-to-end product story.
```

#### Page subheadline (lines 113-116)
```
This capstone worked because the team split responsibility clearly, then pulled the work
back together into a single system across modeling, documentation, deployment, and presentation.
```

#### TEAM array (lines 10-56) - 5 member cards
```
{ name:"AKASH",         fullName:"Akash Anipakalu Giridhar",
  role:"ML Engineering and Library Architecture",
  detail:"Built and patched the breezeml package, shaped the sparse inference pipeline,
          and deployed the Flask serving layer used by the app.",
  glowColor:"red" }

{ name:"SUBASREE",      fullName:"Subasree Segar",
  role:"Data Science and Model Evaluation",
  detail:"Ran evaluation across both tasks, read the failure patterns at the class level,
          and translated model behavior into report-grade findings.",
  glowColor:"blue" }

{ name:"VISHAL",        fullName:"Vishal Shaileshkumar Rathod",
  role:"Feature Engineering",
  detail:"Designed and validated the TF-IDF feature space, tested vocabulary and n-gram settings,
          and kept the sparse pipeline effective.",
  glowColor:"orange" }

{ name:"SRILAXMI",      fullName:"Srilaxmi Ganjipalli",
  role:"Data Exploration and Preprocessing",
  detail:"Mapped the raw dataset structure, identified imbalance and cleaning issues,
          and clarified the data constraints the models had to survive.",
  glowColor:"green" }

{ name:"TSERENNADMID",  fullName:"Tserennadmid Batkhuu",
  role:"Reporting and Documentation",
  detail:"Maintained repository continuity, documented the weekly project state,
          and kept the team narrative coherent as the system evolved.",
  glowColor:"purple" }
```

#### STRIP array (lines 58-63) - operating snapshot stats
```
{ label:"People",         value:"5" }
{ label:"Core workstreams", value:"5" }
{ label:"Shared outcome", value:"1 shipped system" }
{ label:"Operating mode", value:"Cross-functional" }
```

#### Team doctrine section (lines 160-166)
```
headline: "No isolated heroics. Shared system ownership."
body: "The strongest part of the team was not that every member did the same kind of work..."
```

#### External links (lines 193-209)
- GitHub: `https://github.com/venomez-viper/Classification-Project`
- PyPI: `https://pypi.org/project/breezeml/`

---

### 5. Journey Page
**File:** `frontend/components/Journey.tsx`

#### Page headline (lines 137-140)
```
The deep-learning route was real,
but the production answer came from discipline.
```

#### Page subheadline (lines 142-145)
```
This is the story of timeouts, memory ceilings, imbalance, augmentation, and the moment
a simpler model proved stronger than the louder one.
```

#### STATS array (lines 20-25) - pressure map cards
```
{ label:"Rows touched",       value:"42K+" }
{ label:"Training ceiling",   value:"1+ hour epochs" }
{ label:"GPU reality",        value:"RTX 3050 / 4GB" }
{ label:"Final decision",     value:"SVM wins" }
```

#### PHASES array (lines 27-78) - 5 numbered phase cards
```
01. eyebrow:"Infrastructure shock"
    title: "Colab looked convenient until the workload hit back."
    description: "The original DeBERTa plan started in Google Colab, but the dataset volume..."
    impact: "Cloud convenience broke before the experiment matured."

02. eyebrow:"Compute discipline"
    title: "A local Windows GPU became the lab, with almost no room for waste."
    description: "Training moved onto a single RTX 3050 with 4GB of VRAM..."
    impact: "Every batch became an engineering choice, not a default setting."

03. eyebrow:"Truth in the labels"
    title: "The real enemy was not tooling. It was class imbalance."
    description: "The model kept collapsing toward dominant classes..."
    impact: "The neural network learned the majority too quickly and the edge cases barely at all."

04. eyebrow:"Intervention mode"
    title: "We built extra data pressure instead of pretending the dataset was fair."
    description: "Minority classes were expanded with generated long-form descriptions using a local flan-t5-base workflow..."
    impact: "The data track became engineered, not merely collected."

05. eyebrow:"Final verdict"
    title: "The LLM was respectable. The cascade SVM was production-ready."
    description: "DeBERTa reached 64% Macro F1, which proved the training work was real. But the V3
                  Meta-Ensemble reached 81.02% Macro F1 on Task 1 and 55.41% on 428 sub-industries..."
    impact: "The cascade system won because it read the taxonomy hierarchy instead of ignoring it."
```

#### TAKEAWAYS array (lines 80-96) - 3 summary cards
```
1. title:"Constraint-aware engineering"
   text: "This page is about what happens when model ambition meets hardware, time, and real label imbalance."

2. title:"Experimentation with consequences"
   text: "Each phase changed the next one. Tooling, metrics, augmentation, and deployment all fed into the decision."

3. title:"A product-minded ending"
   text: "The journey mattered because it ended in a deployable choice, not just an interesting notebook result."
```

#### Final decision section (lines 288-317)
```
headline: "The ending was not anti-LLM. It was pro-evidence."

Left card (winner):
  title: "4-Level Cascade SVM"
  score: "81.02%"
  label: "Task 1 · +13.90 pp over rubric threshold"
  body:  "Sector → Group → MSTAR → Sub-Industry. Reads the Morningstar taxonomy hierarchy
          instead of flattening it. 40× faster than DeBERTa on CPU, +24.90 pp better on Macro F1.
          Task 2 reaches 55.41% across 428 sub-industry classes."

Right card (contender):
  title: "DeBERTa-v3 Small"
  score: "64.00%"
  body:  "Valuable as an experiment, useful for learning, and proof that the team could stand up a harder stack.
          But it did not beat the classical pipeline on the metric that actually mattered."
```

---

### 6. How It Works Section (shared component)
**File:** `frontend/components/HowItWorks.tsx`
> Used on: home page (compact mode) and about page (full mode)

#### Section headline (line 86)
```
One description. Four decisions. One industry route.
```

#### Section subheadline (lines 88-91)
```
GECS-Sage routes text through the Morningstar hierarchy instead of flattening the full taxonomy
into one opaque decision. The current build is honest about the audit: V13 is the deployable
Task 1 baseline, and Task 2 is constrained by the Task 1 parent.
```

#### Stats row (lines 96-103) - full mode only
```
{ n:"53,587", label:"company segments",      sub:"case-issued training corpus" }
{ n:"145",    label:"GECS industry codes",   sub:"Task 1 class space" }
{ n:"428",    label:"sub-industry codes",    sub:"Task 2 constrained children" }
```

#### CASCADE_LEVELS array (lines 9-38) - 4 level cards
```
L1: name:"Sector"       classes:11  example:"Financial Services"
L2: name:"Group"        classes:30  example:"Banks"
L3: name:"Industry"     classes:145 example:"Regional Banks"
L4: name:"Sub-Industry" classes:428 example:"Retail Banking"
```

#### WALK array (lines 40-46) - live walk-through example
```
Input: "The company provides retail mortgage loans and deposit accounts in community banking markets."
L1:    "Financial Services"
L2:    "Banks"
L3:    "Regional Banks, code 10320020"
L4:    "Retail Banking, constrained Task 2 child"
```
> To change the example industry, update the Input text and all 4 L1-L4 values to match.

#### BENCHMARKS array (lines 48-52) - bar chart
```
{ label:"V3 Meta-Ensemble baseline", pct:81.02, note:"deployable Task 1", hero:true }
{ label:"ModernBERT v1",             pct:63.72, note:"A100 full run",     hero:false }
{ label:"Baseline run",              pct:67.18, note:"deprecated",        hero:false }
```

#### Task 1 card (lines 163-175)
```
score: "81.02%"
label: "V3 Meta-Ensemble Macro F1"
body:  "The V3 Meta-Ensemble baseline is reproducible and fully documented, achieving 81.02% F1 score."
```

#### Task 2 card (lines 178-192)
```
score: "55.44%"
label: "Macro F1 across 428 classes"
body:  "Task 2 uses the predicted Task 1 industry as a hard constraint, then ranks only the valid
        sub-industry children for that parent."
note:  "Oracle ceiling: 62.26%"
```

---

### 7. HF Demo Page (new)
**File:** `frontend/app/hf/page.tsx`

#### Page header
```
Tag:      "Hugging Face Space"
HF URL:   "https://akash-ag-gecs-classifier-space.hf.space"
Headline: "GECS Industry Classifier"
Subhead:  "Paste any company description - the model maps it to one of 145 Morningstar GECS
           industry codes, then narrows it to a 428-class sub-industry."
```

#### EXAMPLES array - 6 preset buttons
```
1. label:"Tech - Chips"     text:"The company designs graphics processing units..."
2. label:"Finance - Banking" text:"JPMorgan Chase operates as a global financial..."
3. label:"Healthcare - Pharma" text:"Pfizer discovers, develops, and commercializes..."
4. label:"Energy - Oil & Gas"  text:"ExxonMobil explores, produces, and refines..."
5. label:"Tech - Software"  text:"The company sells cloud-based enterprise software..."
6. label:"Defence"          text:"The firm builds fighter jets, missiles, and radar..."
```

---

### 8. LLM Demo Page (existing, leave wiring alone)
**File:** `frontend/components/LLMDemo.tsx`

#### Telemetry bar text (lines 209-213)
```
MODEL:       DEBERTA-V3-SMALL
PARAMS:      180,000,000
ACCELERATOR: CUDA:0
STATUS:      SYSTEM STATUS: ONLINE
```

#### Page headline (lines 224-228)
```
"Write it in plain English."
"DeBERTa gets it."
```

#### Page subheadline (lines 229-234)
```
"TF-IDF needs exact financial keywords. A transformer reads the meaning of your sentence -
even if you never use a single piece of industry jargon."
```

#### EXAMPLES array (lines 19-44) - 6 preset buttons
```
1. label:"Plain English - Chips"    text:"The company designs tiny silicon chips..."
2. label:"Plain English - Banking"  text:"The business takes deposits from regular people..."
3. label:"Plain English - Medicine" text:"Scientists at this company spend years in laboratories..."
4. label:"Plain English - Energy"   text:"Workers drill deep holes into the earth..."
5. label:"Plain English - Software" text:"The company sells software that helps large businesses..."
6. label:"Plain English - Defence"  text:"The firm builds fighter jets, missiles, and radar systems..."
```

#### PIPELINE array (lines 46-51) - 4 animated steps shown during inference
```
1. label:"Raw text"             detail:"Any natural language description"
2. label:"Tokenisation"         detail:"DeBERTa SentencePiece, 128K vocab"
3. label:"12 attention layers"  detail:"Cross-word meaning, not keywords"
4. label:"Classification head"  detail:"Softmax over 145 Morningstar codes"
```

#### TERMINAL_LOGS array (lines 53-67) - fake terminal output shown during loading
> Update these if you change the model name or hardware.

---

### 9. Navigation
**File:** `frontend/components/Navigation.tsx`

#### NAV links (lines 10-14)
```js
{ label:"Home",    href:"/" }
{ label:"Journey", href:"/journey" }
{ label:"Team",    href:"/team" }
```
> To add the HF demo page to nav, insert: `{ label:"Classifier", href:"/hf" }`

---

### 10. Hugging Face Space Backend
**File:** `hf_space/app.py`

#### Page title / branding (lines 270-278)
```
title:  "TAVSS - GECS Industry Classifier"
header: "TAVSS - GECS Industry Classifier"
sub:    "MGT 599 Capstone · Group 4 · DePaul University"
```

#### Status badges (lines 262-264)
```
T1_BADGE = "145 classes · cascade SVM"   (shown when model loaded)
T2_BADGE = "428 classes · 55.44% F1"     (shown when model loaded)
```

#### Gradio examples (lines 253-260)
```
1. "Apple Inc. designs and sells consumer electronics..."
2. "JPMorgan Chase operates as a global financial services firm..."
3. "NVIDIA designs graphics processing units..."
4. "ExxonMobil explores, produces, and refines petroleum products..."
5. "Pfizer discovers, develops, and commercializes biopharmaceutical products..."
6. "The company operates a network of community banks providing commercial lending..."
```

---

## WHAT'S OUTDATED - SUGGESTED UPDATES

The following values appear inconsistent or need review before the next deployment:

| Item | Shown on site | Notes |
|------|--------------|-------|
| Task 1 F1 | `81.02%` on Hero + HowItWorks + Journey, but `67.99%` on About page | Decide which is the canonical claim and make it consistent |
| Task 1 baseline label | `V3 Meta-Ensemble` on some pages, `V13` on about page | Pick one label |
| Task 2 F1 | `55.44%` vs `55.41%` (minor rounding) | Pick one |
| Serving API | About page still says `localhost:5003` | Update to Hugging Face Space URL |
| breezeml version badge | `v0.2.5` on home PAGES array | Update if new version published |
| DeBERTa score | `64%` / `64.00%` | Consistent across Journey |
| HF demo nav link | Not in Navigation | Add `/hf` to NAV array in `Navigation.tsx` if you want it visible |

---

## HOW AN AGENT SHOULD APPLY UPDATES

1. **Single metric change** (e.g. update F1 score): Search for the old value in the file listed in this doc, replace with new value. Cross-check the "Site-wide constants" table for all files that also reference it.

2. **Update a team member bio**: Find the TEAM array in the relevant component file, change the `detail` or `role` string for that member's object.

3. **Add a new section or page**: Create the file under `frontend/app/<route>/page.tsx` following the same pattern as existing pages (import Navigation, wrap in `<main>`).

4. **Add HF demo to navigation**: In `Navigation.tsx`, add `{ label: "Classifier", href: "/hf" }` to the NAV array (line 10-14).

5. **Change all university/course references**: Do a project-wide find-replace on `DePaul University`, `MGT 599`, `Group 4` strings.
