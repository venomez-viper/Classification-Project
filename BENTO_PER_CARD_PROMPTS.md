# Descriptive Analytics — ultra-modern Apple-style chart prompts ("Our Company" bento, Slide 5)

Rule for every prompt: **bare chart only** — no card, no border, no title bar (the bento card is the
frame). Background pure **#0B0B0F**, edge-to-edge. Generate at the AR shown, then in PowerPoint:
click card picture → **Crop ▸ Fill**. Numbers are baked in; retype in PPT if any drift.

Locked numbers: 53,585 records · 23,207 companies · 145 industries · 428 sub-industries ·
top industry 2,359 / rarest 28 → ~84× imbalance · top sub 2,018 · descriptions 400–800 chars
(cap ~800) · 35.1% multi-segment · 55.2% ambiguous.

## ✦ APPLE STYLE CORE (already embedded in each prompt — for reference)
> Award-winning Apple Keynote product-reveal data visualization, Jony-Ive minimalism. Pure obsidian
> #0B0B0F background. San Francisco / SF Pro Display typography, perfect kerning, generous negative
> space. Refined micro-gradients, frosted-glass depth, soft volumetric key light, gentle bloom, true
> blacks, cinematic 10-bit HDR color. Retina-sharp, anti-aliased, museum-grade, tasteful, classy,
> 4K UHD. No clutter, no 3D bevels, no skeuomorphism — clean and modern.

## Card map (Slide 5)
| Card | AR | Put | Gen AR |
|---|---|---|---|
| Center big | 2.03 | **Industry long-tail (HERO)** | 21:9 |
| Top-center | 2.51 | Sub-industry long-tail | 21:9 |
| Bottom-left wide | 2.10 | Description-length histogram | 21:9 |
| Bottom-right wide | 2.02 | KPI trio strip | 21:9 |
| Top-left square | 1.00 | Segments donut | 1:1 |
| Top-right square | 0.96 | KPI "23,207 Companies" | 1:1 |
| Left-mid | 1.59 | KPI "53,585 Records" | 3:2 |
| Right tall | 0.63 | Vertical KPI stack | 2:3 |

---

### ⭐ HERO · Industry long-tail (center big, 21:9)
```
Award-winning Apple Keynote product-reveal data visualization, Jony-Ive minimalism: a wide
horizontal long-tail bar chart of 145 industry classes, bare (no card, no border, no title bar).
A few tall bars on the left rendered in a refined electric-blue #0A84FF to cyan #64D2FF micro-
gradient with soft volumetric glow, elegantly decaying into a long whisper-thin luminous tail.
Tallest bar annotated "2,359 (4.4%)", tail annotated "rarest 28", one tasteful frosted-glass chip
"~84× imbalance · 145 GECS classes". Hair-thin gridlines, no axis clutter. Pure obsidian #0B0B0F
background edge-to-edge, San Francisco / SF Pro Display typography, true blacks, gentle bloom,
cinematic 10-bit HDR, retina-sharp, museum-grade, classy, 4K UHD, aspect ratio 21:9. Just the chart.
```

### Sub-industry long-tail (top-center, 21:9)
```
Award-winning Apple Keynote data visualization, Jony-Ive minimalism: a wide long-tail bar chart of
428 sub-industry classes, bare (no card/border/title). One dominant tall bar in a refined teal
#64D2FF to indigo #5E5CE6 micro-gradient with soft glow, annotated "2,018", followed by a steep,
elegant drop into a very long flat tail of tiny bars, annotated "dozens = 1 example". Hair-thin
gridlines. Pure obsidian #0B0B0F background edge-to-edge, SF Pro Display typography, frosted-glass
depth, gentle bloom, cinematic 10-bit HDR, retina-sharp, classy, 4K UHD, aspect ratio 21:9. Just
the chart.
```

### Description-length histogram (bottom-left wide, 21:9)
```
Award-winning Apple Keynote data visualization, Jony-Ive minimalism: a histogram of company-
description character length, bare (no card/border/title). Smooth amber #FF9F0A to coral micro-
gradient bars with a delicate glowing distribution curve gliding over them. X-axis 0–800, mass
concentrated 400–800 with a clean hard cap at ~800. One small caption "Description length (chars)
· capped ~800". Hair-thin gridlines, pure obsidian #0B0B0F background edge-to-edge, SF Pro Display,
soft volumetric light, cinematic 10-bit HDR, retina-sharp, classy, 4K UHD, aspect ratio 21:9. Just
the chart.
```

### Segments donut (top-left square, 1:1)
```
Award-winning Apple Keynote data visualization, Jony-Ive minimalism: an elegant thin-ring donut,
bare (no card/border/title). "Single-segment 64.9%" in emerald #30D158 and "Multi-segment 35.1%"
in violet #BF5AF2, smooth luminous HDR gradient ring with soft bloom, a large refined center
numeral "35.1%" with delicate sub-label "multi-segment", one tiny note "55.2% rows ambiguous".
Pure obsidian #0B0B0F background edge-to-edge, SF Pro Display typography, frosted-glass depth, true
blacks, cinematic 10-bit HDR, retina-sharp, classy, 4K UHD, aspect ratio 1:1. Just the chart.
```

### KPI trio strip (bottom-right wide, 21:9)
```
Award-winning Apple Keynote product-reveal layout, Jony-Ive minimalism: three KPI stats in a row,
bare (no card/border). "23,207 Companies", "53,585 Records", "428 Sub-industries" — each a large
refined glowing numeral with a small label and an ultra-minimal line icon, perfectly aligned with
generous spacing. Subtle HDR accents (electric blue, teal, violet). Pure obsidian #0B0B0F background
edge-to-edge, SF Pro Display typography, soft bloom, true blacks, cinematic 10-bit HDR, retina-sharp,
classy, 4K UHD, aspect ratio 21:9. Just the stats.
```

### Single KPI tile (square 1:1; use 3:2 for left-mid)
```
Award-winning Apple Keynote product-reveal stat, Jony-Ive minimalism: a single KPI, bare (no
card/border). A huge refined glowing numeral "23,207" with a small label "COMPANIES" and one ultra-
minimal line icon, centered with generous negative space. Pure obsidian #0B0B0F background edge-to-
edge, SF Pro Display typography, electric-blue #0A84FF HDR glow, soft bloom, true blacks, retina-
sharp, classy, 4K UHD, aspect ratio 1:1. Just the stat.
```
Swap per card: `53,585 / RECORDS` (3:2), `145 / INDUSTRIES`, `428 / SUB-INDUSTRIES`.

### Vertical KPI stack (right tall, 2:3)
```
Award-winning Apple Keynote layout, Jony-Ive minimalism: a vertical stack of four KPI stats, bare
(no card/border). Top to bottom "23,207 Companies", "53,585 Records", "145 Industries", "428 Sub-
industries", evenly spaced — each a refined glowing numeral with a small label and an ultra-minimal
line icon. Subtle multi-color HDR accents. Pure obsidian #0B0B0F background edge-to-edge, SF Pro
Display typography, soft bloom, true blacks, cinematic 10-bit HDR, retina-sharp, classy, 4K UHD,
aspect ratio 2:3 portrait. Just the stats.
```
