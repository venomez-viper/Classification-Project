"""
Exhibit generator (v2) for the GECS / TAVSS capstone master report.
McKinsey-style exhibit system: kicker + action title + rule + source line +
takeaway annotations. All numbers are the honest, company-disjoint figures.
Output: 170-dpi PNGs in this directory, named exhibit_*.png.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
import numpy as np

# ---- Palette ---------------------------------------------------------------
NAVY  = "#0B2A4A"
BLUE  = "#1F6FEB"
STEEL = "#5B7E9E"
TEAL  = "#1AA89C"
GRAY  = "#97A1AD"
LGRID = "#E6EBF0"
INK   = "#2B3742"
RED   = "#C0392B"
GREEN = "#2E9E5B"
GOLD  = "#D99000"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Calibri", "Arial", "DejaVu Sans"],
    "font.size": 10.5,
    "axes.edgecolor": GRAY, "axes.linewidth": 0.7,
    "text.color": INK, "axes.labelcolor": INK,
    "xtick.color": INK, "ytick.color": INK,
    "figure.dpi": 170, "savefig.dpi": 170,
    "savefig.bbox": "tight", "savefig.facecolor": "white",
    "savefig.pad_inches": 0.06,
})

W = 9.6  # standard exhibit width (in)

def new_exhibit(height, top_in=1.18, bot_in=0.62, left=0.085, right=0.965):
    """Create a figure + single axes with reserved header/footer bands."""
    fig = plt.figure(figsize=(W, height))
    H = height
    B = bot_in / H
    Ht = 1 - (top_in + bot_in) / H
    ax = fig.add_axes([left, B, right - left, Ht])
    return fig, ax

def chrome(fig, ax, kicker, title, subtitle=None, source=None):
    H = fig.get_figheight()
    pos = ax.get_position()
    def fy(inch): return pos.y1 + inch / H
    fig.add_artist(Line2D([pos.x0, pos.x1], [fy(0.86)] * 2,
                   transform=fig.transFigure, color=NAVY, lw=2.6, solid_capstyle="butt"))
    fig.text(pos.x0, fy(0.98), kicker, fontsize=9, fontweight="bold",
             color=BLUE, va="bottom")
    fig.text(pos.x0, fy(0.52), title, fontsize=14.5, fontweight="bold",
             color=NAVY, va="bottom")
    if subtitle:
        fig.text(pos.x0, fy(0.16), subtitle, fontsize=10, color=INK, va="bottom")
    if source:
        fig.add_artist(Line2D([pos.x0, pos.x1], [pos.y0 - 0.30 / H] * 2,
                       transform=fig.transFigure, color=LGRID, lw=0.9))
        fig.text(pos.x0, pos.y0 - 0.52 / H, source, fontsize=7.4, color=GRAY, va="top")

def cleanbars(ax, ygrid=True):
    for s in ["top", "right", "left"]:
        ax.spines[s].set_visible(False)
    ax.tick_params(length=0)
    if ygrid:
        ax.set_axisbelow(True)
        ax.yaxis.grid(True, color=LGRID, lw=0.9)

# ============================================================================
# Exhibit 1 — KPI hero band
# ============================================================================
def exhibit_kpi():
    fig, ax = new_exhibit(3.0, top_in=1.15, bot_in=0.5)
    ax.axis("off"); ax.set_xlim(0, 6); ax.set_ylim(0, 1)
    cards = [
        ("75.0%", "Task 1 Macro F1", "145 industries", NAVY),
        ("91.4%", "Top-3 accuracy", "shortlist hit rate", BLUE),
        ("55.44%", "Task 2 Macro F1", "428 sub-industries", TEAL),
        ("109x", "vs random", "baseline 0.69%", STEEL),
        ("10,717", "held-out rows", "company-disjoint", GRAY),
    ]
    n = len(cards); gap = 0.04; cw = (6 - gap * (n - 1)) / n
    for i, (big, lab, sub, col) in enumerate(cards):
        x = i * (cw + gap)
        ax.add_patch(FancyBboxPatch((x, 0.04), cw, 0.92,
                     boxstyle="round,pad=0.005,rounding_size=0.02",
                     facecolor="#F4F7FA", edgecolor="none", zorder=1))
        ax.add_patch(Rectangle((x, 0.04), 0.035, 0.92, facecolor=col, zorder=2))
        ax.text(x + cw / 2 + 0.01, 0.62, big, ha="center", va="center",
                fontsize=21, fontweight="bold", color=col)
        ax.text(x + cw / 2 + 0.01, 0.34, lab, ha="center", va="center",
                fontsize=9.5, fontweight="bold", color=INK)
        ax.text(x + cw / 2 + 0.01, 0.18, sub, ha="center", va="center",
                fontsize=8, color=GRAY)
    chrome(fig, ax, "EXHIBIT 1",
           "The system at a glance: an audited 75.0% on the hardest metric",
           "Final results on a company-disjoint hold-out the model never saw in training.",
           "Source: TAVSS final evaluation, task1_test.csv (10,717 rows); CASCADE_AUDIT.md.")
    fig.savefig("exhibit_kpi.png"); plt.close(fig)

# ============================================================================
# Exhibit 2 — Waterfall: the honesty correction
# ============================================================================
def exhibit_waterfall():
    fig, ax = new_exhibit(4.5)
    steps = [
        ("V1 reported\n(leaked)", 88.90, RED, "abs"),
        ("Remove\nleakage", -29.25, GRAY, "delta"),
        ("V2 honest\nbaseline", 59.65, NAVY, "abs"),
        ("Hybrid +\nensemble", 8.77, BLUE, "delta"),
        ("ModernBERT\n+ calibration", 6.58, BLUE, "delta"),
        ("Final\n(locked)", 75.0, NAVY, "abs"),
    ]
    x = np.arange(len(steps)); running = 0; prev_top = 0
    for i, (lab, val, col, kind) in enumerate(steps):
        if kind == "abs":
            ax.bar(i, val, width=0.6, color=col, zorder=3)
            top = val
            if i == 0:
                ax.bar(i, val, width=0.6, color="none", hatch="////",
                       edgecolor="white", zorder=4)
            ax.text(i, val + 1.4, f"{val:.1f}", ha="center", fontweight="bold",
                    color=col, fontsize=10.5)
            running = val
        else:
            base = running
            ax.bar(i, val, width=0.6, bottom=base, color=col, zorder=3)
            sign = "+" if val >= 0 else ""
            ytxt = max(base, base + val) + 1.4
            ax.text(i, ytxt, f"{sign}{val:.1f}", ha="center",
                    fontweight="bold", color=INK, fontsize=10)
            running = base + val
            top = running
        if i > 0:
            ax.plot([i - 1 + 0.3, i - 0.3], [prev_top, base if kind == "delta" else prev_top],
                    color=GRAY, lw=0.8, ls=(0, (3, 2)), zorder=2)
        prev_top = top
    ax.axhline(75, color=GOLD, ls=(0, (5, 3)), lw=1.2, zorder=1)
    ax.text(2.5, 77.6, "75% case bar", color=GOLD, fontsize=8.6, ha="center", fontweight="bold")
    ax.annotate("the number we deleted", xy=(0, 70), xytext=(1.4, 96),
                fontsize=8.8, color=RED, ha="center", fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=RED, lw=1.1,
                                connectionstyle="arc3,rad=0.2"))
    ax.set_xticks(x); ax.set_xticklabels([s[0] for s in steps], fontsize=8.8)
    ax.set_ylim(0, 100); ax.set_ylabel("Macro F1 (%)"); ax.set_yticks(range(0, 101, 25))
    cleanbars(ax)
    chrome(fig, ax, "EXHIBIT 2",
           "We deleted 29 points of leakage, then earned 15 back honestly",
           "From a leaked 88.9% to a true 59.7% baseline, rebuilt to a defensible 75.0%.",
           "Source: CASCADE_AUDIT.md; docs/model_version_history.md. Bars: levels; segments: changes.")
    fig.savefig("exhibit_waterfall.png"); plt.close(fig)

# ============================================================================
# Exhibit 3 — Model journey
# ============================================================================
def exhibit_journey():
    fig, ax = new_exhibit(4.4)
    labels = ["V2\nbaseline", "V5\nhybrid", "V8\nensemble", "MBERT\nbase",
              "MBERT\nlarge", "2x large\nensemble", "Final\ncalibrated"]
    vals = [59.65, 67.11, 68.42, 67.18, 70.29, 73.95, 75.0]
    cols = [GRAY, STEEL, STEEL, BLUE, BLUE, NAVY, NAVY]
    x = np.arange(len(vals))
    ax.bar(x, vals, width=0.62, color=cols, zorder=3)
    ax.plot(x, vals, color=NAVY, lw=1.0, alpha=0.35, zorder=2, marker="o", ms=3)
    for xi, v, c in zip(x, vals, cols):
        ax.text(xi, v + 1.1, f"{v:.1f}", ha="center", fontweight="bold", color=c, fontsize=9.6)
    ax.axhline(75, color=GOLD, ls=(0, (5, 3)), lw=1.2)
    ax.text(0.0, 76.2, "75% case bar", color=GOLD, fontsize=8.6, fontweight="bold")
    ax.annotate("transformers break\nthe classical wall", xy=(4, 70.3), xytext=(2.7, 50),
                fontsize=8.6, color=NAVY, ha="center", style="italic",
                arrowprops=dict(arrowstyle="->", color=NAVY, lw=1))
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=8.7)
    ax.set_ylim(0, 88); ax.set_ylabel("Macro F1 (%)"); ax.set_yticks(range(0, 81, 20))
    cleanbars(ax)
    chrome(fig, ax, "EXHIBIT 3",
           "Every gain after the reset is real, and earned the hard way",
           "Engineered features carried the classical track; the transformer broke the ceiling.",
           "Source: docs/model_version_history.md. All bars on the company-disjoint test set.")
    fig.savefig("exhibit_journey.png"); plt.close(fig)

# ============================================================================
# Exhibit 4 — Leakage anatomy
# ============================================================================
def exhibit_leakage():
    fig, ax = new_exhibit(4.0)
    pos = ax.get_position()
    ax.axis("off")
    axL = fig.add_axes([pos.x0, pos.y0, 0.40, pos.height])
    axR = fig.add_axes([pos.x0 + 0.52, pos.y0, 0.40, pos.height])
    # left: composition
    axL.barh([0], [97.2], color=RED, zorder=3)
    axL.barh([0], [2.8], left=[97.2], color=GREEN, zorder=3)
    axL.text(48.6, 0, "97.2% already\nseen in training", ha="center", va="center",
             color="white", fontsize=10, fontweight="bold")
    axL.text(98.6, 0.62, "2.8%\nunseen", ha="center", color=GREEN, fontsize=8.5, fontweight="bold")
    axL.set_xlim(0, 100); axL.set_ylim(-0.7, 1.1); axL.set_yticks([])
    axL.set_xticks([0, 50, 100]); axL.set_xlabel("Share of 10,717 test rows (%)", fontsize=9)
    for s in ["top", "right", "left"]:
        axL.spines[s].set_visible(False)
    axL.tick_params(length=0)
    # right: scores
    names = ["Reported\n(leaked)", "Unseen rows\nonly", "Honest\nbaseline"]
    vals = [88.90, 81.73, 59.65]; cols = [RED, GOLD, NAVY]
    axR.bar(range(3), vals, width=0.6, color=cols, zorder=3)
    for xi, v in zip(range(3), vals):
        axR.text(xi, v + 1.6, f"{v:.2f}", ha="center", fontweight="bold", fontsize=9.6)
    axR.set_xticks(range(3)); axR.set_xticklabels(names, fontsize=8.8)
    axR.set_ylim(0, 100); axR.set_ylabel("Macro F1 (%)", fontsize=9); axR.set_yticks(range(0, 101, 25))
    cleanbars(axR)
    chrome(fig, ax, "EXHIBIT 4",
           "The 88.9% was memory, not skill",
           "Almost the entire test set had been seen in training; the honest score is 59.65%.",
           "Source: CASCADE_AUDIT.md. Same model architecture, evaluated three ways.")
    fig.savefig("exhibit_leakage.png"); plt.close(fig)

# ============================================================================
# Exhibit 5 — 4-level architecture
# ============================================================================
def exhibit_architecture():
    fig, ax = new_exhibit(5.0, top_in=1.18, bot_in=0.55)
    ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off")
    rows = [
        ("Company / segment description", "free-text input", "#E6EBF0", INK),
        ("L1   Sector head", "11 classes", STEEL, "white"),
        ("L2   Industry-group head", "55 classes", BLUE, "white"),
        ("L3   Industry code   (Task 1)", "145 GECS codes   .   75.0% Macro F1", NAVY, "white"),
        ("L4   Sub-industry cascade   (Task 2)", "428 codes, constrained to L3 parent   .   55.44%", TEAL, "white"),
    ]
    y = 9.3; h = 1.32; gap = 0.52; x0, w = 0.6, 7.0
    tops = []
    for title, sub, fc, tc in rows:
        ax.add_patch(FancyBboxPatch((x0, y - h), w, h,
                     boxstyle="round,pad=0.02,rounding_size=0.10",
                     linewidth=0, facecolor=fc, zorder=3))
        ax.text(x0 + 0.32, y - h / 2 + 0.20, title, color=tc, fontsize=11.5,
                fontweight="bold", va="center", zorder=4)
        ax.text(x0 + 0.32, y - h / 2 - 0.30, sub, color=tc, fontsize=9, va="center",
                zorder=4, alpha=0.93)
        tops.append(y - h); y -= (h + gap)
    for t in tops[:-1]:
        ax.add_patch(FancyArrowPatch((x0 + w / 2, t), (x0 + w / 2, t - gap),
                     arrowstyle="-|>", mutation_scale=15, color=GRAY, lw=1.6, zorder=2))
    # brace label
    ax.add_patch(FancyBboxPatch((x0 + w + 0.35, tops[3] - 0.05), 2.0, h + 2 * (h + gap) - 0.5,
                 boxstyle="round,pad=0.02,rounding_size=0.06", facecolor="#F4F7FA",
                 edgecolor=LGRID, zorder=1))
    ax.text(x0 + w + 1.35, tops[2] - 0.2, "one shared\nModernBERT-large\nencoder,\n3 joint heads",
            fontsize=8.6, color=NAVY, va="center", ha="center", style="italic", zorder=2)
    chrome(fig, ax, "EXHIBIT 5",
           "One model, four decisions: the taxonomy is the architecture",
           "Levels 1 to 3 are joint heads on a shared encoder; Level 4 is gated by the L3 prediction.",
           "Source: hf_space_modernbert/app.py; scripts/train_cascade_t2.py.")
    fig.savefig("exhibit_architecture.png"); plt.close(fig)

# ============================================================================
# Exhibit 6 — cascade level accuracy, leaked vs honest
# ============================================================================
def exhibit_levels():
    fig, ax = new_exhibit(4.2)
    levels = ["L1 sector\n(11 classes)", "L2 group\n(55 classes)", "L3 industry\n(145 classes)"]
    leaked = [93.48, 91.00, 88.90]; honest = [80.59, 70.75, 59.65]
    x = np.arange(3); w = 0.36
    ax.bar(x - w / 2, leaked, w, color=RED, zorder=3, label="With leakage")
    ax.bar(x + w / 2, honest, w, color=NAVY, zorder=3, label="Honest (company-disjoint)")
    for xi, v in zip(x - w / 2, leaked):
        ax.text(xi, v + 1.2, f"{v:.1f}", ha="center", fontweight="bold", color=RED, fontsize=9)
    for xi, v in zip(x + w / 2, honest):
        ax.text(xi, v + 1.2, f"{v:.1f}", ha="center", fontweight="bold", color=NAVY, fontsize=9)
    for xi, a, b in zip(x, leaked, honest):
        ax.annotate(f"-{a-b:.0f} pts", xy=(xi, b + (a - b) / 2), ha="center",
                    fontsize=8, color=GRAY, style="italic")
    ax.set_xticks(x); ax.set_xticklabels(levels)
    ax.set_ylim(0, 105); ax.set_ylabel("Accuracy / Macro F1 (%)"); ax.set_yticks(range(0, 101, 25))
    ax.legend(frameon=False, fontsize=9, loc="lower left", bbox_to_anchor=(0, -0.02))
    cleanbars(ax)
    chrome(fig, ax, "EXHIBIT 6",
           "The leak widens, and the error compounds, at every level",
           "A wrong sector makes every finer decision unreachable: ~52% of errors start at L1.",
           "Source: CASCADE_AUDIT.md, cascade level-by-level evaluation.")
    fig.savefig("exhibit_levels.png"); plt.close(fig)

# ============================================================================
# Exhibit 7 — TF-IDF ceiling
# ============================================================================
def exhibit_tfidf():
    fig, ax = new_exhibit(3.9)
    names = ["Segment text only", "LongProfile only", "Word + char n-grams",
             "Combined word", "Both vectorizers stacked"]
    vals = [39.06, 46.92, 55.56, 54.97, 57.49]
    order = np.argsort(vals); names = [names[i] for i in order]; vals = [vals[i] for i in order]
    cols = [STEEL] * 4 + [NAVY]; y = np.arange(len(vals))
    ax.barh(y, vals, color=cols, zorder=3, height=0.62)
    for yi, v in zip(y, vals):
        ax.text(v + 0.6, yi, f"{v:.2f}", va="center", fontweight="bold", fontsize=9.4)
    ax.axvline(59.65, color=GOLD, ls=(0, (5, 3)), lw=1.2)
    ax.text(60.1, 0.0, "even the best\nstacked TF-IDF\nstops here", color=GOLD,
            fontsize=8.2, fontweight="bold", va="center")
    ax.set_yticks(y); ax.set_yticklabels(names, fontsize=9)
    ax.set_xlim(0, 72); ax.set_xlabel("Macro F1 (%)")
    for s in ["top", "right", "left"]:
        ax.spines[s].set_visible(False)
    ax.tick_params(length=0); ax.set_axisbelow(True); ax.xaxis.grid(True, color=LGRID, lw=0.9)
    chrome(fig, ax, "EXHIBIT 7",
           "Bag-of-words hits a wall near 57%, whatever you feed it",
           "Vocabulary size, char n-grams, and stacking all converge; the limit is representational.",
           "Source: CASCADE_AUDIT.md, TF-IDF ablation on the company-disjoint split.")
    fig.savefig("exhibit_tfidf.png"); plt.close(fig)

# ============================================================================
# Exhibit 8 — calibration audit
# ============================================================================
def exhibit_calibration():
    fig, ax = new_exhibit(3.9)
    names = ["Per-class thresholds\ntuned on test", "5-fold cross-\nvalidation", "Temperature scaling\n(locked headline)"]
    vals = [77.51, 73.96, 75.0]; cols = [RED, GRAY, NAVY]
    notes = ["overfit to test\nnot reported", "honest,\nno real lift", "generalizes,\ndisclosed"]
    x = np.arange(3)
    ax.bar(x, vals, width=0.52, color=cols, zorder=3)
    for xi, v, n in zip(x, vals, notes):
        ax.text(xi, v + 0.5, f"{v:.2f}", ha="center", fontweight="bold", fontsize=9.6)
        ax.text(xi, 5.5, n, ha="center", fontsize=8.3, color="white", fontweight="bold")
    ax.set_xticks(x); ax.set_xticklabels(names, fontsize=9)
    ax.set_ylim(0, 84); ax.set_ylabel("Macro F1 (%)"); ax.set_yticks(range(0, 81, 20))
    cleanbars(ax)
    chrome(fig, ax, "EXHIBIT 8",
           "We reported the defensible number, not the highest one",
           "77.51% was overfit to the test set; cross-validation exposed it. We locked 75.0%.",
           "Source: docs/model_version_history.md, calibration audit.")
    fig.savefig("exhibit_calibration.png"); plt.close(fig)

# ============================================================================
# Exhibit 9 — final scorecard
# ============================================================================
def exhibit_scorecard():
    fig, ax = new_exhibit(3.9)
    pos = ax.get_position(); ax.axis("off")
    axL = fig.add_axes([pos.x0, pos.y0, 0.46, pos.height])
    axR = fig.add_axes([pos.x0 + 0.58, pos.y0, 0.34, pos.height])
    m = ["Macro F1", "Top-3 acc.", "Top-5 acc."]; v = [75.0, 91.4, 95.3]
    axL.bar(range(3), v, width=0.55, color=[NAVY, BLUE, STEEL], zorder=3)
    for xi, val in zip(range(3), v):
        axL.text(xi, val + 1.4, f"{val:.1f}%", ha="center", fontweight="bold", fontsize=9.5)
    axL.set_xticks(range(3)); axL.set_xticklabels(m, fontsize=9)
    axL.set_ylim(0, 108); axL.set_yticks(range(0, 101, 25)); axL.set_ylabel("(%)", fontsize=9)
    cleanbars(axL)
    axL.set_title("Task 1  (145 industries)", fontsize=9.5, color=NAVY, fontweight="bold", loc="left")
    axR.bar([0, 1], [75.0, 55.44], width=0.5, color=[NAVY, TEAL], zorder=3)
    for xi, val in zip([0, 1], [75.0, 55.44]):
        axR.text(xi, val + 1.4, f"{val:.2f}%", ha="center", fontweight="bold", fontsize=9.5)
    axR.set_xticks([0, 1]); axR.set_xticklabels(["Task 1\n145", "Task 2\n428"], fontsize=9)
    axR.set_ylim(0, 100); axR.set_yticks(range(0, 101, 25))
    cleanbars(axR)
    axR.set_title("Macro F1 by task", fontsize=9.5, color=NAVY, fontweight="bold", loc="left")
    chrome(fig, ax, "EXHIBIT 9",
           "Wrong on the first guess, usually right by the third",
           "Top-3 accuracy of 91.4% is the number that governs an analyst-review workflow.",
           "Source: TAVSS final evaluation. Random baseline for Task 1 is 0.69%.")
    fig.savefig("exhibit_scorecard.png"); plt.close(fig)

# ============================================================================
# Exhibit 10 — structural ceiling
# ============================================================================
def exhibit_ceiling():
    fig, ax = new_exhibit(3.9)
    pos = ax.get_position(); ax.axis("off")
    axL = fig.add_axes([pos.x0, pos.y0, 0.44, pos.height])
    axR = fig.add_axes([pos.x0 + 0.56, pos.y0, 0.36, pos.height])
    comp = [45.3, 25.5, 15.9, 13.3]; clab = ["single", "2 codes", "3 codes", "4+ codes"]
    ccol = [GREEN, STEEL, BLUE, RED]
    axL.bar(range(4), comp, color=ccol, width=0.64, zorder=3)
    for xi, vv in zip(range(4), comp):
        axL.text(xi, vv + 0.9, f"{vv:.1f}%", ha="center", fontweight="bold", fontsize=9)
    axL.set_xticks(range(4)); axL.set_xticklabels(clab, fontsize=9)
    axL.set_ylim(0, 55); axL.set_ylabel("Share of test rows (%)", fontsize=9)
    cleanbars(axL)
    axL.set_title("Codes per company", fontsize=9.5, color=NAVY, fontweight="bold", loc="left")
    axR.axis("off")
    facts = [("35.1%", "of companies are multi-code\nconglomerates"),
             ("55.2%", "of rows carry inherent\nlabel ambiguity"),
             ("~52%", "of errors start at the\nL1 sector decision")]
    yy = 0.9
    for big, small in facts:
        axR.text(0.0, yy, big, fontsize=18, fontweight="bold", color=NAVY,
                 transform=axR.transAxes, va="center")
        axR.text(0.34, yy, small, fontsize=9, color=INK, transform=axR.transAxes, va="center")
        yy -= 0.34
    chrome(fig, ax, "EXHIBIT 10",
           "The ceiling is in the data, not the model",
           "Most rows belong to conglomerates whose shared text is correct for several codes at once.",
           "Source: data/cleaned/task1_clean.csv composition; CASCADE_AUDIT.md.")
    fig.savefig("exhibit_ceiling.png"); plt.close(fig)

# ============================================================================
# Exhibit 11 — sector 310 confusion (ranking)
# ============================================================================
def exhibit_sector310():
    fig, ax = new_exhibit(3.7)
    pairs = ["Industrials -> Consumer Cyclical", "Industrials -> Consumer Defensive",
             "Industrials -> Real Estate", "Industrials -> Technology"]
    vals = [60, 57, 51, 43]
    y = np.arange(len(vals))[::-1]
    ax.barh(y, vals, color=RED, height=0.6, zorder=3, alpha=0.92)
    for yi, v in zip(y, vals):
        ax.text(v + 0.8, yi, f"{v}", va="center", fontweight="bold", fontsize=9.5, color=RED)
    ax.set_yticks(y); ax.set_yticklabels(pairs, fontsize=9)
    ax.set_xlim(0, 70); ax.set_xlabel("Misclassified test rows")
    for s in ["top", "right", "left"]:
        ax.spines[s].set_visible(False)
    ax.tick_params(length=0); ax.set_axisbelow(True); ax.xaxis.grid(True, color=LGRID, lw=0.9)
    chrome(fig, ax, "EXHIBIT 11",
           "One sector generates the costliest confusions",
           "Diversified Industrials describe many businesses at once, so they scatter across sectors.",
           "Source: CASCADE_AUDIT.md, top L1 confusion pairs (sector 310).")
    fig.savefig("exhibit_sector310.png"); plt.close(fig)

# ============================================================================
# Exhibit 12 — Task 2 toward the oracle ceiling
# ============================================================================
def exhibit_task2():
    fig, ax = new_exhibit(3.9)
    names = ["Flat\n428-way", "Constrained\nto parent", "Segment-aware\nvectorizer", "Final\ncascade"]
    vals = [20.0, 42.1, 51.2, 55.44]; cols = [GRAY, STEEL, BLUE, TEAL]
    x = np.arange(4)
    ax.bar(x, vals, width=0.6, color=cols, zorder=3)
    ax.plot(x, vals, color=NAVY, lw=1.0, alpha=0.35, marker="o", ms=3, zorder=2)
    for xi, v in zip(x, vals):
        ax.text(xi, v + 1.2, f"{v:.2f}" if v % 1 else f"{v:.0f}", ha="center",
                fontweight="bold", fontsize=9.5)
    ax.axhline(62.26, color=GOLD, ls=(0, (5, 3)), lw=1.3)
    ax.text(3.45, 63.4, "oracle ceiling 62.3 (if Task 1 were perfect)", color=GOLD,
            fontsize=8.4, ha="right", fontweight="bold")
    ax.annotate("captures ~89% of the\nreachable headroom", xy=(3, 55.44), xytext=(1.5, 30),
                fontsize=8.4, color=NAVY, ha="center", style="italic",
                arrowprops=dict(arrowstyle="->", color=NAVY, lw=1))
    ax.set_xticks(x); ax.set_xticklabels(names, fontsize=8.8)
    ax.set_ylim(0, 72); ax.set_ylabel("Macro F1 (%)"); ax.set_yticks(range(0, 71, 20))
    cleanbars(ax)
    chrome(fig, ax, "EXHIBIT 12",
           "Task 2: structure turns an impossible 428-way problem into a solved one",
           "Constraining sub-industries to the Task 1 parent lifts the score from ~20% to 55.4%.",
           "Source: docs/model_version_history.md, Task 2 progression; oracle = perfect-Task-1 ceiling.")
    fig.savefig("exhibit_task2.png"); plt.close(fig)

# ============================================================================
# Exhibit 13 — deployment architecture
# ============================================================================
def exhibit_deploy():
    fig, ax = new_exhibit(4.4, top_in=1.18, bot_in=0.55)
    ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off")

    def box(x, y, w, h, title, sub, fc, tc, badge=None):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.10",
                     linewidth=0, facecolor=fc, zorder=3))
        ax.text(x + w / 2, y + h - 0.42, title, ha="center", color=tc, fontsize=10.5,
                fontweight="bold", zorder=4)
        ax.text(x + w / 2, y + 0.34, sub, ha="center", color=tc, fontsize=8.2, zorder=4, alpha=0.93)
        if badge:
            ax.text(x + w / 2, y + h / 2 - 0.05, badge, ha="center", color=tc, fontsize=8,
                    style="italic", zorder=4)

    box(0.4, 4.1, 2.1, 1.9, "Browser", "user / API client", "#E6EBF0", INK)
    box(3.3, 4.1, 2.6, 1.9, "Vercel", "Next.js 15 frontend . 5 proxy routes", BLUE, "white")
    ax.text(4.6, 3.78, "maxDuration = 60s (absorbs cold starts)", fontsize=7.3,
            color=GRAY, ha="center", style="italic")
    box(6.9, 6.0, 2.7, 1.85, "HF Space  (transformer)", "ModernBERT-large . FastAPI + Gradio", NAVY, "white")
    box(6.9, 2.1, 2.7, 1.85, "HF Space  (classical)", "SVM cascade . fallback", TEAL, "white")

    for (x1, y1, x2, y2) in [(2.5, 5.05, 3.3, 5.05), (5.9, 5.5, 6.9, 6.7), (5.9, 4.6, 6.9, 3.3)]:
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                     mutation_scale=14, color=GRAY, lw=1.6, zorder=2,
                     connectionstyle="arc3,rad=0.05"))
    ax.text(2.9, 5.45, "POST /api/predict", fontsize=7.6, color=GRAY, ha="center")
    ax.text(6.5, 6.25, "warm path", fontsize=7.4, color=GRAY, ha="center", rotation=16)
    ax.text(8.25, 1.75, "cold start 20-60s on first call", fontsize=7.2, color=GRAY, ha="center")
    chrome(fig, ax, "EXHIBIT 13",
           "Two layers so a slow model never takes the product down",
           "The browser only ever talks to Vercel; the proxy absorbs Hugging Face cold starts.",
           "Source: frontend/ (Vercel) and hf_space_modernbert/app.py (Hugging Face).")
    fig.savefig("exhibit_deploy.png"); plt.close(fig)

if __name__ == "__main__":
    exhibit_kpi(); exhibit_waterfall(); exhibit_journey(); exhibit_leakage()
    exhibit_architecture(); exhibit_levels(); exhibit_tfidf(); exhibit_calibration()
    exhibit_scorecard(); exhibit_ceiling(); exhibit_sector310(); exhibit_task2()
    exhibit_deploy()
    print("All exhibits written (13).")
