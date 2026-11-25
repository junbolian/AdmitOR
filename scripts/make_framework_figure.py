"""Framework figure of the paper (figures/fig0_framework.pdf and .png): (a) the certifier as a pipeline of stages, with the stage
at which each error enters; (b) value functions of three programs over one
parameter, showing why agreement and resampling detect a modeling error and
not a data error.

Usage: python scripts/make_framework_figure.py   (needs pdflatex with the
mathptmx, amsmath, and amssymb packages)."""
import os
import numpy as np
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "figures")
import matplotlib
matplotlib.use("pgf")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, RegularPolygon, Circle, Rectangle, Polygon

plt.rcParams.update({
    "pgf.texsystem": "pdflatex", "pgf.rcfonts": False, "text.usetex": True,
    "pgf.preamble": r"\usepackage[T1]{fontenc}\usepackage{mathptmx}\usepackage{amsmath}\usepackage{amssymb}",
    "font.family": "serif", "font.size": 8, "axes.linewidth": 0.5,
    "xtick.major.width": 0.5, "ytick.major.width": 0.5, "xtick.major.size": 2.5, "ytick.major.size": 0,
})
INK, SUB = "#1f2933", "#6b7280"
FAM = {"A": "#3b6ea5", "B": "#c9772f", "C": "#21957a"}
DATA, MODEL, VER = "#b5493f", "#6a5aa6", "#8a8f98"
TINT = {"text": "#f6f6f6", "A": "#eaf2fc", "prog": "#f7f7f7", "agree": "#f7f7f7", "check": "#f7f7f7"}

W_IN, H_IN = 6.75, 2.05
fig = plt.figure(figsize=(W_IN, H_IN))
AW = 0.665
ax = fig.add_axes([0.0, 0.0, AW, 1.0])
XMAX = 100.0
YMAX = XMAX * H_IN / (AW * W_IN)
ax.set_xlim(0, XMAX); ax.set_ylim(0, YMAX); ax.set_aspect("equal"); ax.axis("off")
bx = fig.add_axes([0.725, 0.21, 0.265, 0.68])

CY, CH, CW = 22.0, 17.0, 13.6          # card centre height, card height, card width


def card(xc, title, ec="#374151", fc="#f8f9fb", lw=1.0):
    ax.add_patch(FancyBboxPatch((xc - CW / 2, CY - CH / 2), CW, CH, boxstyle="round,pad=0,rounding_size=1.6",
                                ec=ec, fc=fc, lw=lw, zorder=2))
    ax.text(xc, CY + CH / 2 - 1.6, r"\textbf{" + title + "}", ha="center", va="top", fontsize=7.5, color=INK, zorder=5)


def arrow(p0, p1, color=INK, ls="-", lw=0.9):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=7, lw=lw, color=color, ls=ls,
                                 zorder=1, shrinkA=0, shrinkB=0))


def hexbadge(x, y, f, r=2.5):
    ax.add_patch(RegularPolygon((x, y), 6, radius=r, orientation=0, fc=FAM[f], ec="white", lw=0.8, zorder=6))
    ax.text(x, y - 0.05, rf"\textsf{{{f}}}", ha="center", va="center", fontsize=6.8, color="white", zorder=7)


def document(x, y, w=6.4, h=8.0):
    pts = [(x - w / 2, y - h / 2), (x + w / 2, y - h / 2), (x + w / 2, y + h / 2 - 2.0),
           (x + w / 2 - 2.0, y + h / 2), (x - w / 2, y + h / 2)]
    ax.add_patch(Polygon(pts, closed=True, fc="white", ec="#5b6b80", lw=0.8, zorder=4))
    for k in range(4):
        yy = y + h / 2 - 2.6 - 1.45 * k
        ax.plot([x - w / 2 + 1.1, x + w / 2 - (1.6 if k == 0 else 1.1)], [yy, yy], color="#5b6b80", lw=0.7, zorder=5)


def table(x, y, highlight=(), w=7.2, h=5.6, rows=3, cols=3):
    cw, rh = w / cols, h / rows
    for i in range(rows):
        for j in range(cols):
            fc = "#f3d6d2" if (i, j) in highlight else "white"
            ax.add_patch(Rectangle((x - w / 2 + j * cw, y + h / 2 - (i + 1) * rh), cw, rh, fc=fc,
                                   ec="#5b6b80", lw=0.6, zorder=4))


xs = [8.5, 27.5, 46.5, 65.5, 84.5]
# 1 text
card(xs[0], r"Text $x$")
document(xs[0], CY - 1.6)
# 2 extraction
card(xs[1], r"Extract $\hat\theta$")
table(xs[1] + 0.6, CY - 2.3, highlight=((1, 2), (2, 2)))
hexbadge(xs[1] - 4.6, CY + 1.6, "A", r=2.2)
# 3 programs
card(xs[2], "Programs")
for (dx, dy, f) in ((0.0, 2.2, "A"), (-3.6, -3.6, "B"), (3.6, -3.6, "C")):
    hexbadge(xs[2] + dx, CY - 1.2 + dy, f, r=2.6)
# 4 agreement: clique of three values
card(xs[3], "Agree")
P = {"A": (xs[3], CY + 1.4), "B": (xs[3] - 3.7, CY - 4.4), "C": (xs[3] + 3.7, CY - 4.4)}
ax.add_patch(Polygon([P["A"], P["B"], P["C"]], closed=True, fc="#eef1f5", ec="#5b6b80", lw=0.9, zorder=4))
for f, (px, py) in P.items():
    ax.add_patch(Circle((px, py), 1.25, fc=FAM[f], ec="white", lw=0.7, zorder=5))
# 5 check
card(xs[4], r"Check $\hat\theta$")
table(xs[4] - 1.4, CY - 0.9, w=6.0, h=4.6)
ax.add_patch(Circle((xs[4] + 2.4, CY - 3.4), 2.0, fc="none", ec="#374151", lw=0.9, zorder=6))
ax.plot([xs[4] + 3.8, xs[4] + 5.4], [CY - 4.8, CY - 6.4], color="#374151", lw=1.4, solid_capstyle="round", zorder=6)
hexbadge(xs[4] - 4.4, CY - 6.4, "B", r=1.7)
hexbadge(xs[4] - 1.0, CY - 6.4, "C", r=1.7)

for k in range(4):
    arrow((xs[k] + CW / 2, CY), (xs[k + 1] - CW / 2, CY))

# outcomes: certify above, abstain below the last stage
def pill(x, y, label, fc, ec, mark):
    ax.add_patch(FancyBboxPatch((x - 7.2, y - 2.3), 14.4, 4.6, boxstyle="round,pad=0,rounding_size=2.3",
                                ec=ec, fc=fc, lw=1.0, zorder=3))
    ax.text(x - 4.6, y, mark, ha="center", va="center", fontsize=8, color=ec, zorder=4)
    ax.text(x + 1.4, y, r"\textbf{" + label + "}", ha="center", va="center", fontsize=7.3, color=INK, zorder=4)
pill(84.5, CY + CH / 2 + 6.2, r"certify $v$", "#e7f1ec", "#3f7d5c", r"$\checkmark$")
pill(84.5, CY - CH / 2 - 6.2, "abstain", "#f1f2f4", "#6b7280", r"$\times$")
arrow((84.5, CY + CH / 2), (84.5, CY + CH / 2 + 3.9), color="#3f7d5c")
arrow((84.5, CY - CH / 2), (84.5, CY - CH / 2 - 3.9), color=SUB)
# disagreement also leads to abstention
ax.plot([65.5, 65.5, 77.3], [CY - CH / 2, CY - CH / 2 - 6.2, CY - CH / 2 - 6.2], color=SUB, lw=0.9, zorder=1)
arrow((76.5, CY - CH / 2 - 6.2), (77.3, CY - CH / 2 - 6.2), color=SUB)

# where the errors enter
def mark(x0, x1, y, color, label):
    ax.plot([x0, x0, x1, x1], [y + 1.0, y, y, y + 1.0], color=color, lw=1.0, solid_capstyle="butt", zorder=3)
    ax.text((x0 + x1) / 2, y - 0.8, label, ha="center", va="top", fontsize=7.2, color=color)
mark(xs[1] - CW / 2, xs[1] + CW / 2, CY - CH / 2 - 2.2, DATA, r"data error $\delta$")
mark(xs[2] - CW / 2, xs[2] + CW / 2, CY - CH / 2 - 2.2, MODEL, r"modeling error $\rho$")
ax.text(xs[1], CY - CH / 2 - 6.4, "shared by all programs", ha="center", va="top", fontsize=6.6, color=DATA)
ax.text(xs[2], CY - CH / 2 - 6.4, "one program each", ha="center", va="top", fontsize=6.6, color=MODEL)
ax.text(0.2, YMAX - 0.4, "(a)", ha="left", va="top", fontsize=9)

# ---- panel (b): value functions over one parameter
t = np.linspace(0, 1, 400)
V = 2.0 + 1.6 * t
pc = np.where((t > 0.62) & (t < 0.9), V + 0.9 * np.sin(np.pi * (t - 0.62) / 0.28), V)
th_true, th_hat = 0.28, 0.46
bx.axvspan(0.62, 0.9, color="#efedf6", lw=0, zorder=0)
bx.plot(t, V, color=FAM["A"], lw=2.4, zorder=2, solid_capstyle="butt")
bx.plot(t, V, color=FAM["B"], lw=1.1, zorder=3, ls=(0, (4, 2)))
bx.plot(t, pc, color=FAM["C"], lw=1.1, zorder=4)
bx.axvline(th_true, color=INK, lw=0.6, ls=(0, (1, 1.5)), zorder=1)
bx.axvline(th_hat, color=DATA, lw=0.8, zorder=1)
bx.plot([th_true], [2.0 + 1.6 * th_true], "o", ms=4, mfc="white", mec=INK, mew=0.8, zorder=5)
bx.plot([th_hat], [2.0 + 1.6 * th_hat], "o", ms=4, mfc=DATA, mec=DATA, zorder=5)
for s in (0.15, 0.55, 0.72, 0.83):
    bx.plot([s], [1.62], marker="|", ms=6, color=SUB, mew=0.8, zorder=5, clip_on=False)
bx.set_xlim(0, 1); bx.set_ylim(1.55, 4.7)
bx.set_xticks([th_true, th_hat]); bx.set_xticklabels([r"$\theta(x)$", r"$\hat\theta$"])
bx.get_xticklabels()[1].set_color(DATA)
bx.set_yticks([])
for s in ("top", "right"):
    bx.spines[s].set_visible(False)
bx.set_xlabel(r"parameter $\theta$", color=INK, labelpad=1)
bx.set_ylabel(r"optimal value", color=INK)
bx.text(0.76, 4.55, r"$\Delta$", ha="center", va="center", fontsize=8.5, color=MODEL)
bx.text(0.99, 3.36, r"$p_{\mathrm{A}},p_{\mathrm{B}}$", ha="right", va="top", fontsize=7.5, color=INK)
bx.text(0.86, 4.25, r"$p_{\mathrm{C}}$", ha="left", va="bottom", fontsize=7.5, color=FAM["C"])
bx.set_title("(b)", loc="left", fontsize=9, pad=3, x=-0.12)
os.makedirs(OUT, exist_ok=True)
fig.savefig(os.path.join(OUT, "fig0_framework.pdf"), bbox_inches="tight", pad_inches=0.02)
fig.savefig(os.path.join(OUT, "fig0_framework.png"), dpi=220, bbox_inches="tight", pad_inches=0.02)
