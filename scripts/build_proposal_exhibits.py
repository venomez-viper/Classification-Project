"""Generate publication-quality PNG exhibits for the McKinsey-style proposal."""
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from matplotlib.patches import FancyBboxPatch, Rectangle, FancyArrowPatch
from matplotlib import rcParams

ROOT = Path(__file__).resolve().parents[1]
OUT  = ROOT / "docs" / "proposal_exhibits"
OUT.mkdir(parents=True, exist_ok=True)

# ── McKinsey-ish palette ──
NAVY    = "#1F3A5F"
TEAL    = "#0E6B6E"
CORAL   = "#E07856"
GOLD    = "#D4A93F"
SAGE    = "#7A9E7E"
LIGHT_GRAY = "#E8ECEF"
DARK_GRAY  = "#3D4951"

rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.edgecolor": DARK_GRAY,
    "axes.labelcolor": DARK_GRAY,
    "xtick.color": DARK_GRAY,
    "ytick.color": DARK_GRAY,
    "axes.spines.top": False,
    "axes.spines.right": False,
})


def save(name: str):
    path = OUT / name
    plt.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"  {path}")


# ─────────────────────────────────────────────────────────────────────────────
# EXHIBIT 1 — Performance journey (the audit story)
# ─────────────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(11, 5.2))

models = [
    "Original\ncascade\n(leaked)",
    "Same model\non truly\nunseen rows",
    "Honest\nTF-IDF\ncascade",
    "TF-IDF +\nengineered\nnumerical",
    "MiniLM\nembeddings",
    "V5 hybrid",
    "V6 BGE\nhybrid",
    "V8 mega-\nensemble",
    "V10 calib.\nstack",
    "V13 GECS\nanchors",
    "V14 RAC",
    "V16 FinBERT\n(Colab)",
]
scores = [88.90, 81.73, 59.65, 63.42, 59.70, 67.11, 67.70, 68.42, 69.09, 67.99, 66.04, 61.84]
colors = [CORAL, GOLD, NAVY, NAVY, NAVY, NAVY, NAVY, NAVY, TEAL, NAVY, NAVY, NAVY]

bars = ax.bar(range(len(models)), scores, color=colors, edgecolor="white", linewidth=1.2, width=0.75)
for bar, sc in zip(bars, scores):
    ax.text(bar.get_x() + bar.get_width()/2, sc + 1.2, f"{sc:.1f}",
             ha="center", va="bottom", fontsize=9, color=DARK_GRAY, fontweight="bold")

# Reference lines
ax.axhline(75, color=GOLD, linestyle="--", linewidth=1, alpha=0.6)
ax.text(len(models) - 0.5, 75.6, "Case target: 75%", color=GOLD, fontsize=8.5,
         ha="right", fontweight="bold")
ax.axhline(69.09, color=TEAL, linestyle=":", linewidth=1, alpha=0.5)
ax.text(0, 70, "Honest best: 69.09%", color=TEAL, fontsize=8.5, fontweight="bold")

ax.set_xticks(range(len(models)))
ax.set_xticklabels(models, fontsize=8.5)
ax.set_ylabel("Macro F1 (%)", fontsize=10.5, color=DARK_GRAY)
ax.set_ylim(0, 100)
ax.set_yticks(np.arange(0, 101, 20))

ax.set_title("Exhibit 1: Honest performance clusters around 68–69%; the 88.90% was leakage.",
              fontsize=11.5, color=NAVY, loc="left", fontweight="bold", pad=14)

# Subtle annotation for leaked vs honest
ax.annotate("", xy=(0.5, 86), xytext=(1.5, 80),
             arrowprops=dict(arrowstyle="->", color=GOLD, lw=1.2))
ax.text(2, 84, "After leakage audit:\n−7pp on truly unseen rows",
         fontsize=8.5, color=GOLD, fontweight="bold")

# Legend
legend_handles = [
    mpatches.Patch(color=CORAL, label="Leaked baseline (invalid)"),
    mpatches.Patch(color=GOLD,  label="Truly unseen subset"),
    mpatches.Patch(color=NAVY,  label="Honest train→test rebuild"),
    mpatches.Patch(color=TEAL,  label="Current honest best"),
]
ax.legend(handles=legend_handles, loc="upper right", frameon=False, fontsize=9)

save("exhibit_1_performance_journey.png")


# ─────────────────────────────────────────────────────────────────────────────
# EXHIBIT 2 — GECS hierarchy (boxes & arrows)
# ─────────────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(11, 4.2))
ax.set_xlim(0, 12); ax.set_ylim(0, 5); ax.axis("off")

levels = [
    ("3 Super Sectors",      "Cyclical / Defensive / Sensitive",          NAVY,  1.5),
    ("11 Sectors",           "Basic Materials, Financial Services, …",    TEAL,  3.6),
    ("55 Industry Groups",   "Banks, REITs, Insurance, …",                 SAGE,  5.7),
    ("145 Industries",       "Banks-Diversified, Banks-Regional, …",       GOLD,  7.8),
    ("450 Business Activities", "Commercial Lending, Mortgage Origin., …", CORAL, 9.9),
]
y = 2.3
for i, (head, sub, color, x) in enumerate(levels):
    box = FancyBboxPatch((x - 0.9, y - 0.7), 1.9, 1.5,
                          boxstyle="round,pad=0.05,rounding_size=0.08",
                          linewidth=1.5, edgecolor=color, facecolor="white")
    ax.add_patch(box)
    ax.text(x, y + 0.45, head, ha="center", va="center",
             fontsize=10.5, color=color, fontweight="bold")
    ax.text(x, y - 0.1, sub, ha="center", va="center",
             fontsize=7.8, color=DARK_GRAY, wrap=True)
    if i < len(levels) - 1:
        arrow = FancyArrowPatch((x + 0.95, y + 0.15), (levels[i+1][3] - 0.95, y + 0.15),
                                arrowstyle="->", mutation_scale=14,
                                color=DARK_GRAY, linewidth=1.2)
        ax.add_patch(arrow)

ax.text(6, 4.4,
         "Exhibit 2: The GECS hierarchy. Errors at the top cascade downward and "
         "compound across 450 leaves.",
         ha="center", fontsize=11.5, color=NAVY, fontweight="bold")
ax.text(6, 0.6,
         "Task 1 predicts the 4th level (145). Task 2 predicts the 5th (450), constrained "
         "by the deterministic Task 1 → Task 2 mapping.",
         ha="center", fontsize=9, color=DARK_GRAY, style="italic")

save("exhibit_2_hierarchy.png")


# ─────────────────────────────────────────────────────────────────────────────
# EXHIBIT 3 — Top-10 class F1 (which classes pass the 85% bar?)
# ─────────────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(11, 4.5))
top10_codes = [
    "10310010\nAsset Management",
    "31030010\nDiversified Inds.",
    "10320020\nRegional Banks",
    "10410020\nReal Estate Svcs.",
    "31040010\nEng. & Const.",
    "31070020\nTrucking",
    "31110020\nIT Services",
    "20525040\nFood Distribution",
    "20620020\nMed. Devices",
    "20610010\nBiotech",
]
v10_f1 = [78.6, 30.7, 90.7, 58.1, 58.1, 47.3, 53.4, 77.1, 77.9, 80.8]
v13_f1 = [79.3, 37.9, 91.1, 67.3, 56.3, 45.9, 53.1, 75.8, 78.3, 78.5]
target = 85

x = np.arange(len(top10_codes))
w = 0.36
b1 = ax.bar(x - w/2, v10_f1, w, label="V10 calibrated stack (current best)",
             color=NAVY, edgecolor="white", linewidth=1.2)
b2 = ax.bar(x + w/2, v13_f1, w, label="V13 with GECS anchors",
             color=TEAL, edgecolor="white", linewidth=1.2)
ax.axhline(target, color=GOLD, linestyle="--", linewidth=1.3, alpha=0.8)
ax.text(len(x) - 0.5, target + 1, "Case requirement: 85%",
         color=GOLD, fontweight="bold", ha="right", fontsize=9)

for bar, sc in zip(b1, v10_f1):
    ax.text(bar.get_x() + bar.get_width()/2, sc + 1, f"{sc:.0f}",
             ha="center", fontsize=7.5, color=NAVY)
for bar, sc in zip(b2, v13_f1):
    ax.text(bar.get_x() + bar.get_width()/2, sc + 1, f"{sc:.0f}",
             ha="center", fontsize=7.5, color=TEAL)

ax.set_xticks(x); ax.set_xticklabels(top10_codes, fontsize=8)
ax.set_ylabel("Per-class F1 (%)")
ax.set_ylim(0, 105)
ax.set_title("Exhibit 3: Only 2/10 top classes clear the 85% bar; "
              "31030010 (conglomerates) drags every model.",
              fontsize=11.5, color=NAVY, loc="left", fontweight="bold", pad=12)
ax.legend(loc="upper right", frameon=False, fontsize=9)
save("exhibit_3_top10_breakdown.png")


# ─────────────────────────────────────────────────────────────────────────────
# EXHIBIT 4 — LongProfile contamination diagnostic
# ─────────────────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(11, 4.3))

# Left: pie of conglomerate vs single-code companies
ax = axes[0]
labels = ["Single-code\ncompanies\n(65%)", "Multi-code\nconglomerates\n(35%)"]
sizes  = [65, 35]
colors_pie = [SAGE, CORAL]
wedges, _ = ax.pie(sizes, colors=colors_pie, startangle=90,
                    wedgeprops=dict(width=0.45, edgecolor="white", linewidth=2))
ax.text(0, 0.05, "35%", ha="center", fontsize=22, fontweight="bold", color=CORAL)
ax.text(0, -0.25, "conglomerates", ha="center", fontsize=9.5, color=DARK_GRAY)

# Outside labels
ax.text(1.15, 0.55, "65% single-code\n(clean signal)",
         ha="left", fontsize=9.5, color=SAGE, fontweight="bold")
ax.text(-1.45, -0.55, "35% multi-code\n(contaminated signal)",
         ha="left", fontsize=9.5, color=CORAL, fontweight="bold")
ax.set_title("Conglomerate share of companies", fontsize=10.5,
              color=NAVY, pad=10, fontweight="bold")

# Right: schematic of the contamination
ax = axes[1]
ax.axis("off")
ax.set_xlim(0, 10); ax.set_ylim(0, 10)

# Heading
ax.text(5, 9.3, "How concatenation manufactures label noise",
         ha="center", fontsize=10.5, color=NAVY, fontweight="bold")

# Three rows showing same LongProfile but different labels
rows = [
    ("LongProfile (same) + Segment A: 'Banking ops'",  "→ Code: 10320010", SAGE),
    ("LongProfile (same) + Segment B: 'Asset mgmt'",   "→ Code: 10310010", GOLD),
    ("LongProfile (same) + Segment C: 'Insurance'",    "→ Code: 10340010", CORAL),
]
for i, (text, label, color) in enumerate(rows):
    y = 7 - i * 1.8
    rect = Rectangle((0.4, y), 6.6, 1.1, facecolor=LIGHT_GRAY,
                      edgecolor=color, linewidth=1.6)
    ax.add_patch(rect)
    ax.text(0.65, y + 0.55, text, fontsize=9, color=DARK_GRAY, va="center")
    ax.text(7.3, y + 0.55, label, fontsize=9, color=color,
             fontweight="bold", va="center")

ax.text(5, 1.1,
         "Result: identical LongProfile prefix → 3 different labels.\n"
         "Same text → 3 contradictory training signals.",
         ha="center", fontsize=9, color=DARK_GRAY, style="italic")

fig.suptitle("Exhibit 4: 35% of companies are multi-segment conglomerates whose "
              "LongProfile maps to multiple GECS codes.",
              fontsize=11.5, color=NAVY, fontweight="bold", y=1.01)
plt.tight_layout()
save("exhibit_4_contamination.png")


# ─────────────────────────────────────────────────────────────────────────────
# EXHIBIT 5 — Recommended architecture
# ─────────────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(11, 5.6))
ax.set_xlim(0, 12); ax.set_ylim(0, 8); ax.axis("off")

ax.text(6, 7.5,
         "Exhibit 5: The Week 5+ architecture removes LongProfile contamination and "
         "predicts the hierarchy jointly.",
         ha="center", fontsize=11.5, color=NAVY, fontweight="bold")

# Stage 1: Input
def box(x, y, w, h, color, title, sub=None, fc="white"):
    b = FancyBboxPatch((x, y), w, h,
                       boxstyle="round,pad=0.05,rounding_size=0.08",
                       linewidth=1.6, edgecolor=color, facecolor=fc)
    ax.add_patch(b)
    ax.text(x + w/2, y + h - 0.35, title, ha="center", va="top",
             fontsize=9.5, color=color, fontweight="bold")
    if sub:
        ax.text(x + w/2, y + 0.3, sub, ha="center", va="bottom",
                 fontsize=7.8, color=DARK_GRAY)

box(0.3, 4.8, 2.0, 1.6, NAVY,  "Clean input",
     "SegmentName +\nSegmentDescription only", fc=LIGHT_GRAY)
box(0.3, 2.5, 2.0, 1.6, NAVY,  "Auxiliary",
     "LongProfile @ 0.3 weight\n5 numerical features", fc=LIGHT_GRAY)

# Arrows to encoder
ax.add_patch(FancyArrowPatch((2.4, 5.6), (3.4, 5.3),
                             arrowstyle="->", mutation_scale=14, color=DARK_GRAY))
ax.add_patch(FancyArrowPatch((2.4, 3.3), (3.4, 4.6),
                             arrowstyle="->", mutation_scale=14, color=DARK_GRAY))

# Encoder
box(3.5, 4.4, 2.5, 1.9, TEAL, "Shared encoder",
     "DeBERTa-v3-base\n(fine-tuned on segments)", fc="white")

# Multi-task heads
heads = [
    (6.5, 5.4, "Sector head (11)",      SAGE,  "α = 0.2"),
    (6.5, 4.0, "Group head (55)",        GOLD,  "β = 0.3"),
    (6.5, 2.6, "Industry head (145)",    CORAL, "γ = 0.5"),
]
for x, y, title, color, w in heads:
    box(x, y, 2.0, 0.9, color, title, sub=w, fc="white")
    ax.add_patch(FancyArrowPatch((6.0, 5.3), (x, y + 0.45),
                                 arrowstyle="->", mutation_scale=12, color=DARK_GRAY,
                                 alpha=0.6))

# Loss
box(8.8, 3.8, 2.6, 1.3, NAVY,
     "Hierarchy-weighted loss",
     "α·CE(sector) + β·CE(group)\n+ γ·CE(industry) + DB loss", fc="white")
ax.add_patch(FancyArrowPatch((8.6, 5.85), (8.8, 4.9),
                             arrowstyle="->", mutation_scale=12, color=DARK_GRAY))
ax.add_patch(FancyArrowPatch((8.6, 4.45), (8.8, 4.45),
                             arrowstyle="->", mutation_scale=12, color=DARK_GRAY))
ax.add_patch(FancyArrowPatch((8.6, 3.05), (8.8, 4.0),
                             arrowstyle="->", mutation_scale=12, color=DARK_GRAY))

# Inference
box(3.5, 0.5, 7.9, 1.3, GOLD,
     "Inference: industry head → Task 1 code → constrain Task 2 to deterministic children",
     "Output: top-3 codes with calibrated probabilities", fc=LIGHT_GRAY)

save("exhibit_5_architecture.png")


# ─────────────────────────────────────────────────────────────────────────────
# EXHIBIT 6 — Cumulative gain stack (the path to 75%)
# ─────────────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(11, 4.5))
stages = [
    "Honest\nbaseline",
    "+ Engineered\nfeatures",
    "+ MiniLM\n& BGE\nembeddings",
    "+ Class\nprototypes\n& GECS\nanchors",
    "+ Segment-\nonly inputs\n(Week 5)",
    "+ Hierarchical\nmulti-task\nDeBERTa",
    "+ Long-tail\nloss\n& retrieval",
    "Target",
]
gains = [59.65, 63.42, 67.70, 69.09, 73, 76, 79, 80]
gains_done = [True, True, True, True, False, False, False, False]

xs = np.arange(len(stages))
for i, (x, g, done) in enumerate(zip(xs, gains, gains_done)):
    color = NAVY if done else GOLD
    alpha = 1.0 if done else 0.55
    bar = ax.bar(x, g, color=color, alpha=alpha, edgecolor="white",
                  linewidth=1.4, width=0.65)
    ax.text(x, g + 1, f"{g:.1f}%", ha="center", fontsize=9.5,
             color=color, fontweight="bold")
    if not done:
        ax.text(x, 5, "planned", ha="center", fontsize=8,
                 color=GOLD, fontweight="bold", style="italic")

ax.axhline(75, color=CORAL, linestyle="--", linewidth=1.2, alpha=0.7)
ax.text(0, 76, "Case threshold: 75%", color=CORAL, fontsize=9, fontweight="bold")

ax.set_xticks(xs); ax.set_xticklabels(stages, fontsize=8.5)
ax.set_ylabel("Cumulative Macro F1 (%)")
ax.set_ylim(0, 90)
ax.set_title("Exhibit 6: The remaining sprint expects ~+10pp from clean inputs + hierarchy + long-tail losses.",
              fontsize=11.5, color=NAVY, loc="left", fontweight="bold", pad=12)
legend_handles = [
    mpatches.Patch(color=NAVY,  label="Achieved"),
    mpatches.Patch(color=GOLD,  alpha=0.55, label="Planned (Weeks 5–7)"),
]
ax.legend(handles=legend_handles, loc="upper left", frameon=False, fontsize=9)

save("exhibit_6_cumulative_gain.png")


print("\nAll exhibits saved to", OUT)
