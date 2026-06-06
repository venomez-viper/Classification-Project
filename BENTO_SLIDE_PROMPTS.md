# Descriptive Analytics — Apple Bento Hero Slide · Nano Banana 4K/HDR Prompts

Hand-picked the 4 EDA graphs that actually drove the understanding, with the **real verified
numbers** from `outputs/figures/*.csv`. Center-horizontal hero + bento tiles, ultra-modern,
4K UHD, 10-bit HDR. Use your `Bento Design Apple Keynote Inspired Background Slides (3).pptx`
as the canvas/style reference.

## ✅ Locked numbers (do not let the model change these)
- **53,585** records · **23,207** companies · **145** industries (Task 1)
- **27,537** records · **428** sub-industries (Task 2)
- Task 1 most common: code `10310010` = **2,359** rows (4.4%); rarest `30920020` = **28** → **~84× imbalance**
- Task 1 #2: `31030010` Diversified Conglomerates = **2,358** (the error magnet)
- Task 2 most common: `3103001001` = **2,018** (7.3%), then a long tail of **singleton** classes (count = 1)
- Company descriptions: most **400–800 characters**, hard cap ~**800**
- **35.1%** multi-segment companies · **55.2%** of rows carry inherent label ambiguity
- Only column with any missing values: `SegmentDescription`

---

## 🎨 Global style token (prepend to every prompt)
```
Ultra-modern data-viz, Apple "Bento box" keynote aesthetic. Pure obsidian background #0B0B0F,
rounded-corner glass cards #15151C with 1px hairline borders #2A2A33 and soft ambient shadows.
SF Pro Display typography, tight kerning. Cinematic 10-bit HDR color, deep blacks, luminous
neon-gradient data, subtle bloom and glassmorphism, fine grid lines, crisp anti-aliased edges.
4K UHD, ultra-sharp, high dynamic range, 16:9. Minimal, premium, lots of negative space.
```

---

# ⭐ MASTER PROMPT — full bento slide in one image (copy-paste)
```
Design one ultra-premium 16:9 keynote slide titled "DESCRIPTIVE ANALYTICS" in an Apple
"Bento box" grid, ultra-modern, 4K UHD, cinematic 10-bit HDR. Pure obsidian #0B0B0F canvas,
rounded glass cards #15151C with hairline borders #2A2A33, soft shadows, SF Pro Display type,
luminous neon-gradient charts, subtle bloom, glassmorphism, fine gridlines, generous spacing.

Top strip: "DESCRIPTIVE ANALYTICS" left, small caption right
"Morningstar GECS · 23,207 companies · 53,585 records".

A row of 4 KPI tiles with huge numerals and tiny icons:
"23,207 Companies", "53,585 Records", "145 Industries", "428 Sub-industries".

CENTER HORIZONTAL HERO card (full width): an ultra-modern descending long-tail bar chart of
145 industry classes — a few tall electric-blue-to-cyan gradient bars on the left collapsing
into a long thin glowing tail; annotate "most common 2,359 rows" on the tallest and
"rarest 28 rows" near the tail, with a callout chip "~84× class imbalance".
Caption: "Industry distribution — long tail across 145 GECS classes".

Bottom row, three equal cards:
1) A donut chart, "Single-segment 64.9%" in emerald #30D158 vs "Multi-segment 35.1%" in
   violet #BF5AF2, big center label "35.1% multi-segment", caption "Segments per company".
2) A smooth right-skewed histogram of company-description length in amber #FF9F0A with a soft
   curve, x-axis 0–800, caption "Description length (chars), capped ~800".
3) A compact long-tail bar chart of 428 sub-industries in teal #64D2FF, tallest annotated
   "2,018" with a long flat tail of singletons, caption "Task 2: 428 sub-industries".

Perfectly aligned grid, ultra-sharp, premium Apple keynote, 4K UHD HDR, 16:9.
```

---

# 🧩 INDIVIDUAL GRAPH PROMPTS (build each card, then drop into the template)

### 1 — HERO · Industry long-tail (the "why this is hard" chart)
```
[global style token]
An ultra-modern horizontal-band hero chart: descending long-tail distribution of 145
industry classes. A handful of tall bars on the left with an electric-blue #0A84FF to cyan
#64D2FF HDR gradient and soft glow, rapidly decaying into a long thin luminous tail. Annotate
the tallest bar "2,359 rows (4.4%)" and the tail "28 rows", with a glowing callout chip
"~84× imbalance across 145 classes". Faint horizontal gridlines, minimal axis, SF Pro labels.
Caption "Industry distribution — long tail across 145 GECS classes". 4K UHD, 10-bit HDR, 16:9.
```

### 2 — Task 2 sub-industry explosion (428 classes, singleton tail)
```
[global style token]
An ultra-modern long-tail bar chart of 428 sub-industry classes in a teal #64D2FF to indigo
#5E5CE6 HDR gradient with soft bloom. One dominant tall bar annotated "3103001001 — 2,018",
then a steep drop into a very long flat tail of tiny bars annotated "dozens of classes with
just 1 example". Title "Task 2: 428 sub-industries", subtle gridlines, premium minimal.
4K UHD, 10-bit HDR, 16:9.
```

### 3 — Description length distribution (signal budget)
```
[global style token]
An ultra-modern histogram of company-description character length, amber #FF9F0A to coral
HDR gradient bars with a smooth glowing KDE overlay curve. X-axis 0 to 800, mass concentrated
between 400 and 800 with a hard cap at ~800. Title "Company description length (characters)",
caption "Most profiles 400–800 chars · truncated at 800". Faint gridlines. 4K UHD, 10-bit HDR, 16:9.
```

### 4 — Segments-per-company donut (ambiguity driver)
```
[global style token]
An ultra-modern thin-ring donut chart: "Single-segment 64.9%" in emerald #30D158 and
"Multi-segment 35.1%" in violet #BF5AF2, glowing HDR gradients, big center numeral "35.1%"
with sub-label "multi-segment". Side note chip "55.2% of rows are inherently ambiguous".
Title "Segments per company". Premium, minimal, glassmorphism. 4K UHD, 10-bit HDR, 16:9.
```

### (Optional 5) — KPI scale tiles only
```
[global style token]
Four ultra-modern Apple bento KPI tiles in a row, each a glass card with a huge glowing
numeral and a tiny line icon: "23,207 Companies", "53,585 Records", "145 Industries",
"428 Sub-industries". HDR neon accents, deep blacks, crisp. 4K UHD, 16:9 strip.
```

---

## 🔩 Workflow
1. In Nano Banana set output to **16:9** and request **4K / highest resolution** each time.
2. Run the **MASTER PROMPT** first; if a card is weak, regenerate just that card with its
   individual prompt and swap it in.
3. Numbers can drift when the model redraws — eyeball the big labels (2,359 · 28 · 84× · 145 ·
   428 · 2,018 · 35.1%) and, if any are wrong, type them over the card in PowerPoint.
4. Drop the final PNG full-bleed onto a blank 16:9 slide (or over your downloaded Bento
   template) in `Group 4 TAVSS FINAL.pptx`.
```
