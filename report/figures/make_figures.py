"""
Exhibit generator for the GECS / TAVSS capstone master report.
All numbers are the honest, company-disjoint figures locked on 2026-05-31.
Output: 200-dpi PNGs in this directory, named exhibit_*.png.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

# ---- House style -------------------------------------------------------------
NAVY  = "#0B2A4A"
BLUE  = "#1F6FEB"
STEEL = "#3D6B99"
TEAL  = "#1AA89C"
GRAY  = "#8A95A3"
LIGHT = "#E8ECF1"
RED   = "#C0392B"
GREEN = "#2E9E5B"
GOLD  = "#D99000"
INK   = "#16202B"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Calibri", "Arial", "DejaVu Sans"],
    "font.size": 11,
    "axes.edgecolor": GRAY,
    "axes.linewidth": 0.8,
    "axes.titlesize": 12,
    "axes.titleweight": "bold",
    "axes.titlecolor": NAVY,
    "text.color": INK,
    "axes.labelcolor": INK,
    "xtick.color": INK,
    "ytick.color": INK,
    "figure.dpi": 200,
    "savefig.dpi": 200,
    "savefig.bbox": "tight",
    "savefig.facecolor": "white",
})

def style_axes(ax, spine_left=True, spine_bottom=True):
    for s in ["top", "right"]:
        ax.spines[s].set_visible(False)
    ax.spines["left"].set_visible(spine_left)
    ax.spines["bottom"].set_visible(spine_bottom)
    ax.tick_params(length=0)

# ---- Exhibit 1: model journey (the honesty correction) -----------------------
def exhibit_1():
    labels = ["V1\ncascade\n(leaked)", "V2\nhonest\nbaseline", "V5\nhybrid",
              "V8\nensemble", "ModernBERT\n-base", "ModernBERT\n-large", "2x large\nensemble", "Final\ncalibrated"]
    vals   = [88.90, 59.65, 67.11, 68.42, 67.18, 70.29, 73.95, 75.0]
    colors = [RED, GRAY, STEEL, STEEL, BLUE, BLUE, NAVY, NAVY]

    fig, ax = plt.subplots(figsize=(9.2, 4.5))
    x = np.arange(len(vals))
    bars = ax.bar(x, vals, width=0.62, color=colors, zorder=3)
    bars[0].set_hatch("////"); bars[0].set_edgecolor("white"); bars[0].set_linewidth(0)

    ax.axhline(75, color=GOLD, ls=(0, (5, 3)), lw=1.4, zorder=2)
    ax.text(3.7, 78.0, "75% case requirement", color=GOLD,
            fontsize=9.5, ha="center", fontweight="bold")

    for xi, v, c in zip(x, vals, colors):
        ax.text(xi, v + 1.2, f"{v:.1f}", ha="center", va="bottom",
                fontsize=10, fontweight="bold", color=c if c != RED else RED)

    ax.annotate("invalid:\ntrain/test leakage", xy=(0, 70), xytext=(1.05, 84),
                fontsize=8.6, color=RED, ha="center", fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=RED, lw=1.1))
    ax.annotate("", xy=(1, 62), xytext=(0.35, 84),
                arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.6,
                                connectionstyle="arc3,rad=-0.25"))
    ax.text(0.62, 50, "honest reset\n-29.3 pts", fontsize=8.6, color=INK,
            ha="center", style="italic")

    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=8.7)
    ax.set_ylim(0, 95); ax.set_ylabel("Macro F1 (%)")
    ax.set_yticks(range(0, 91, 20))
    style_axes(ax)
    ax.set_title("Exhibit 1   Model journey: the honesty correction and the real climb to 75.0%",
                 loc="left", pad=12)
    fig.savefig("exhibit_1_journey.png"); plt.close(fig)

# ---- Exhibit 2: leakage anatomy ---------------------------------------------
def exhibit_2():
    fig, (axL, axR) = plt.subplots(1, 2, figsize=(9.2, 3.9), gridspec_kw={"width_ratios": [1, 1.15]})

    # left: composition of the 10,717-row test set under the leaked split
    seen, unseen = 97.2, 2.8
    axL.barh([0], [seen], color=RED, zorder=3)
    axL.barh([0], [unseen], left=[seen], color=GREEN, zorder=3)
    axL.text(seen / 2, 0, "97.2%\nseen in training", ha="center", va="center",
             color="white", fontsize=10, fontweight="bold")
    axL.text(seen + unseen / 2, 0.55, "2.8% truly\nunseen", ha="center",
             va="bottom", color=GREEN, fontsize=9, fontweight="bold")
    axL.set_xlim(0, 100); axL.set_ylim(-0.6, 1.1)
    axL.set_yticks([]); axL.set_xticks([0, 50, 100])
    axL.set_xlabel("Share of 10,717 test rows (%)")
    for s in ["top", "right", "left"]:
        axL.spines[s].set_visible(False)
    axL.tick_params(length=0)
    axL.set_title("Exhibit 2   Anatomy of the 88.90% number", loc="left", pad=10)

    # right: reported vs honest
    names = ["Reported\n(with leakage)", "Same model,\nunseen rows only", "Honest cascade\nbaseline"]
    vals  = [88.90, 81.73, 59.65]
    cols  = [RED, GOLD, NAVY]
    x = np.arange(3)
    axR.bar(x, vals, width=0.6, color=cols, zorder=3)
    for xi, v in zip(x, vals):
        axR.text(xi, v + 1.5, f"{v:.2f}", ha="center", fontweight="bold", fontsize=10)
    axR.set_xticks(x); axR.set_xticklabels(names, fontsize=8.8)
    axR.set_ylim(0, 100); axR.set_ylabel("Macro F1 (%)")
    axR.set_yticks(range(0, 101, 25))
    style_axes(axR)
    fig.savefig("exhibit_2_leakage.png"); plt.close(fig)

# ---- Exhibit 3: 4-level cascade architecture --------------------------------
def exhibit_3():
    fig, ax = plt.subplots(figsize=(9.2, 4.7))
    ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off")
    rows = [
        ("Company / segment description", "free text input", LIGHT, INK),
        ("L1   Sector head", "11 classes", STEEL, "white"),
        ("L2   Industry-group head", "55 classes", BLUE, "white"),
        ("L3   Industry code   (Task 1)", "145 GECS codes  -  75.0% Macro F1", NAVY, "white"),
        ("L4   Sub-industry cascade   (Task 2)", "428 codes, constrained to L3 parent  -  55.44%", TEAL, "white"),
    ]
    y = 8.7; h = 1.25; gap = 0.62; x0, w = 1.4, 7.2
    centers = []
    for title, sub, fc, tc in rows:
        box = FancyBboxPatch((x0, y - h), w, h, boxstyle="round,pad=0.02,rounding_size=0.12",
                             linewidth=0, facecolor=fc, zorder=3)
        ax.add_patch(box)
        ax.text(x0 + 0.3, y - h / 2 + 0.16, title, color=tc, fontsize=11,
                fontweight="bold", va="center", zorder=4)
        ax.text(x0 + 0.3, y - h / 2 - 0.27, sub, color=tc, fontsize=8.8,
                va="center", zorder=4, alpha=0.92)
        centers.append(y - h)
        y -= (h + gap)
    for top in centers[:-1]:
        ax.add_patch(FancyArrowPatch((x0 + w / 2, top), (x0 + w / 2, top - gap),
                     arrowstyle="-|>", mutation_scale=16, color=GRAY, lw=1.6, zorder=2))
    ax.text(x0 + w + 0.25, centers[3] + h / 2, "multi-task\nModernBERT-large\n(shared encoder,\n3 joint heads)",
            fontsize=8.4, color=NAVY, va="center", ha="left", style="italic")
    ax.text(1.4, 9.5, "Exhibit 3   The 4-level GECS classification cascade",
            fontsize=12, fontweight="bold", color=NAVY)
    fig.savefig("exhibit_3_architecture.png"); plt.close(fig)

# ---- Exhibit 4: final scorecard ---------------------------------------------
def exhibit_4():
    fig, (axL, axR) = plt.subplots(1, 2, figsize=(9.2, 3.7), gridspec_kw={"width_ratios": [1.25, 1]})
    metrics = ["Macro F1", "Top-3 acc.", "Top-5 acc."]
    vals = [75.0, 91.4, 95.3]
    x = np.arange(3)
    axL.bar(x, vals, width=0.55, color=[NAVY, BLUE, STEEL], zorder=3)
    for xi, v in zip(x, vals):
        axL.text(xi, v + 1.4, f"{v:.1f}%", ha="center", fontweight="bold")
    axL.axhline(0.69, color=GRAY, ls=":", lw=1)
    axL.text(2.4, 3.4, "random baseline 0.69%", fontsize=8, color=GRAY, ha="right")
    axL.set_xticks(x); axL.set_xticklabels(metrics)
    axL.set_ylim(0, 105); axL.set_ylabel("(%)"); axL.set_yticks(range(0, 101, 25))
    style_axes(axL)
    axL.set_title("Exhibit 4   Task 1 final scorecard (145 classes)", loc="left", pad=10)

    # right: task 1 vs task 2
    names = ["Task 1\n145 industries", "Task 2\n428 sub-industries"]
    v2 = [75.0, 55.44]
    axR.bar([0, 1], v2, width=0.5, color=[NAVY, TEAL], zorder=3)
    for xi, v in zip([0, 1], v2):
        axR.text(xi, v + 1.4, f"{v:.2f}%", ha="center", fontweight="bold")
    axR.set_xticks([0, 1]); axR.set_xticklabels(names, fontsize=9)
    axR.set_ylim(0, 100); axR.set_ylabel("Macro F1 (%)"); axR.set_yticks(range(0, 101, 25))
    style_axes(axR)
    axR.set_title("Macro F1 by task", loc="left", pad=10)
    fig.savefig("exhibit_4_scorecard.png"); plt.close(fig)

# ---- Exhibit 5: ceiling drivers ---------------------------------------------
def exhibit_5():
    fig, (axL, axR) = plt.subplots(1, 2, figsize=(9.2, 3.7))
    # test-set composition by number of codes per company
    comp = [45.3, 25.5, 15.9, 13.3]
    clab = ["single-code", "2 codes", "3 codes", "4+ codes"]
    ccol = [GREEN, STEEL, BLUE, RED]
    axL.bar(range(4), comp, color=ccol, width=0.62, zorder=3)
    for xi, v in zip(range(4), comp):
        axL.text(xi, v + 0.8, f"{v:.1f}%", ha="center", fontweight="bold", fontsize=9.5)
    axL.set_xticks(range(4)); axL.set_xticklabels(clab, fontsize=9)
    axL.set_ylim(0, 55); axL.set_ylabel("Share of test rows (%)")
    style_axes(axL)
    axL.set_title("Exhibit 5   Why the ceiling is structural", loc="left", pad=10)

    axR.axis("off")
    facts = [
        ("35.1%", "of companies are multi-code\nconglomerates"),
        ("55.2%", "of rows carry inherent\nlabel ambiguity"),
        ("~52%", "of final errors originate at\nthe L1 sector decision"),
    ]
    yy = 0.86
    for big, small in facts:
        axR.text(0.02, yy, big, fontsize=21, fontweight="bold", color=NAVY,
                 transform=axR.transAxes, va="center")
        axR.text(0.32, yy, small, fontsize=9.5, color=INK,
                 transform=axR.transAxes, va="center")
        yy -= 0.34
    fig.savefig("exhibit_5_ceiling.png"); plt.close(fig)

# ---- Exhibit 6: calibration audit -------------------------------------------
def exhibit_6():
    fig, ax = plt.subplots(figsize=(9.2, 3.4))
    names = ["Per-class threshold\ntuning on test", "5-fold cross-\nvalidation", "Temperature scaling\n(locked headline)"]
    vals = [77.51, 73.96, 75.0]
    cols = [RED, GRAY, NAVY]
    x = np.arange(3)
    ax.bar(x, vals, width=0.5, color=cols, zorder=3)
    notes = ["overfit to test\n(not reported)", "honest, no lift", "generalizes,\ndisclosed"]
    for xi, v, n in zip(x, vals, notes):
        ax.text(xi, v + 0.4, f"{v:.2f}", ha="center", fontweight="bold")
        ax.text(xi, 6, n, ha="center", fontsize=8.4, color="white", fontweight="bold")
    ax.set_xticks(x); ax.set_xticklabels(names, fontsize=9)
    ax.set_ylim(0, 82); ax.set_ylabel("Macro F1 (%)"); ax.set_yticks(range(0, 81, 20))
    style_axes(ax)
    ax.set_title("Exhibit 6   Calibration audit: choosing the defensible headline, not the highest number",
                 loc="left", pad=10)
    fig.savefig("exhibit_6_calibration.png"); plt.close(fig)

if __name__ == "__main__":
    exhibit_1(); exhibit_2(); exhibit_3(); exhibit_4(); exhibit_5(); exhibit_6()
    print("All exhibits written.")
