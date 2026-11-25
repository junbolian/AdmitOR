# -*- coding: utf-8 -*-
"""Figures of the paper from the stored tables.

Reads only artifacts/v2/tables (t1_rules.csv, t2_audit.csv) and writes
figures/fig1_agreement_audit.{pdf,png} and figures/fig2_verification_outcome.{pdf,png}.
No model call and no key are needed.

Usage:
    python scripts/make_figures.py [--tables artifacts/v2/tables] [--out figures]

Text is set in Times through pdflatex when it is available, and otherwise in
the Times font of matplotlib's STIX set.
"""
import argparse
import csv
import math
import os
import shutil
import sys

import matplotlib

USE_TEX = shutil.which("pdflatex") is not None
matplotlib.use("pgf" if USE_TEX else "Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

if USE_TEX:
    plt.rcParams.update({
        "pgf.texsystem": "pdflatex", "pgf.rcfonts": False, "text.usetex": True,
        "pgf.preamble": r"\usepackage[T1]{fontenc}\usepackage{mathptmx}",
        "font.family": "serif"})
    PCT = r"\%"
else:
    plt.rcParams.update({"font.family": "STIXGeneral", "mathtext.fontset": "stix"})
    PCT = "%"
plt.rcParams.update({
    "font.size": 8, "axes.linewidth": 0.5, "xtick.major.width": 0.5, "ytick.major.width": 0.5,
    "xtick.major.size": 2.5, "ytick.major.size": 0, "pdf.fonttype": 42})

INK, SUB, GRID, BAND, SLATE = "#191919", "#5f5f5f", "#e6e6e6", "#f3f3f3", "#2f4b63"
CLS = {"D": "#257de0", "E": "#f47230", "P": "#00b894", "B": "#f2a600", "T": "#ee7fac", "U": "#6a4ce2"}
NAMES = {"D": "D  data absent", "E": "E  extraction error", "P": "P  truncated precision",
         "B": "B  label not optimal", "T": "T  text contradicts label", "U": "U  two readings"}
SETS = {"stream": "OptMATH", "confirm": "OptMATH", "calibration": "NANO-CO", "heldout": "NANO-CO"}

# Label-matching three-family certificates withdrawn by the rule "B or C" whose
# flag is correct (the extraction differs from the text, or the text omits the
# data, and the optimum is unchanged). Source: artifacts/v2/audit/AUDIT.md,
# review of the withdrawn label-matching certificates.
CORRECT_FLAGS = {"stream": 2, "confirm": 4, "calibration": 4, "heldout": 0}


def setkey(s):
    for k in SETS:
        if s.startswith(k):
            return k
    raise KeyError(s)


def read(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def fail(msg):
    sys.exit("make_figures.py: " + msg)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tables", default=os.path.join("artifacts", "v2", "tables"))
    ap.add_argument("--out", default="figures")
    a = ap.parse_args()
    t1 = {(setkey(r["set"]), r["rule"]): r for r in read(os.path.join(a.tables, "t1_rules.csv"))}
    t2 = {(setkey(r["set"]), r["stage"]): r for r in read(os.path.join(a.tables, "t2_audit.csv"))}

    def val(k, rule, col):
        return int(t1[(k, rule)][col])

    # ---- counts of panel (a): misses and values per benchmark group
    grp = {"OptMATH": ("stream", "confirm"), "NANO-CO": ("calibration", "heldout")}
    A = {}
    for g, ks in grp.items():
        row = [(sum(val(k, "panel_base_3of3", "label_misses") for k in ks),
                sum(val(k, "panel_base_3of3", "certificates") for k in ks))]
        for f in "ABC":
            row.append((sum(val(k, "single_" + f, "label_misses") - val(k, "panel_base_3of3", "label_misses") for k in ks),
                        sum(val(k, "single_" + f, "certificates") - val(k, "panel_base_3of3", "certificates") for k in ks)))
        A[g] = row
    expect = {"OptMATH": [(53, 405), (23, 32), (14, 51), (33, 66)],
              "NANO-CO": [(9, 176), (26, 37), (19, 67), (23, 67)]}
    if A != expect:
        fail(f"panel (a) counts differ from the paper: {A}")

    # ---- counts of panel (b)
    def classes(ks, stage):
        return {c: sum(int(t2[(k, stage)]["class_" + c]) for k in ks) for c in "DEPBTU"}

    def certs(ks, stage):
        return sum(int(t2[(k, stage)]["certificates"]) for k in ks)

    B = []
    for g, ks in grp.items():
        for stage, lab in (("panel_base_3of3", "agreement"), ("after check (B or C)", "verified")):
            B.append((g, lab, certs(ks, stage), {c: n for c, n in classes(ks, stage).items() if n}))
    expectB = [("OptMATH", "agreement", 405, {"D": 26, "E": 1, "P": 16, "B": 8, "T": 2}),
               ("OptMATH", "verified", 344, {"P": 16, "B": 8, "T": 2}),
               ("NANO-CO", "agreement", 176, {"E": 2, "T": 5, "U": 2}),
               ("NANO-CO", "verified", 169, {"T": 5, "U": 2})]
    if B != expectB:
        fail(f"panel (b) counts differ from the paper: {B}")

    os.makedirs(a.out, exist_ok=True)
    fig1(A, B, a.out)
    fig2(t1, t2, a.out)
    print("wrote", os.path.join(a.out, "fig1_agreement_audit.pdf"), "and",
          os.path.join(a.out, "fig2_verification_outcome.pdf"), "(LaTeX text)" if USE_TEX else "(STIX text)")


def save(fig, out, name):
    fig.savefig(os.path.join(out, name + ".pdf"), bbox_inches="tight", pad_inches=0.02)
    fig.savefig(os.path.join(out, name + ".png"), dpi=200, bbox_inches="tight", pad_inches=0.02)


def fig1(A, B, out):
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(6.75, 1.9), gridspec_kw={"width_ratios": [1.0, 1.12], "wspace": 0.62})
    labels = ["Three families agree", "Family A alone", "Family B alone", "Family C alone"]
    ys = [3.25, 2, 1, 0]
    ax.axhspan(2.72, 3.78, color=BAND, zorder=0, lw=0)
    for i, (y, lab) in enumerate(zip(ys, labels)):
        for (k, n), dy, filled in ((A["OptMATH"][i], 0.17, True), (A["NANO-CO"][i], -0.17, False)):
            p = k / n
            se = math.sqrt(p * (1 - p) / n)
            ax.plot([100 * (p - se), 100 * (p + se)], [y + dy, y + dy], color=SLATE, lw=0.9, zorder=3, solid_capstyle="butt")
            ax.plot(100 * p, y + dy, "o", ms=4.6, mfc=SLATE if filled else "white", mec=SLATE, mew=0.9, zorder=4)
            ax.text(100 * (p + se) + 2.2, y + dy, f"{100 * p:.0f}", ha="left", va="center", color=INK, fontsize=7.5)
    ax.set_yticks(ys)
    ax.set_yticklabels(labels)
    ax.set_xlim(0, 100)
    ax.set_ylim(-0.6, 3.9)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xlabel(f"Returned values that miss the label ({PCT})", color=INK)
    ax.xaxis.grid(True, color=GRID, lw=0.5, zorder=1)
    ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.text(1.0, 2.36, "problems without three-family agreement", fontsize=7, color=SUB, ha="left", va="bottom", style="italic")
    h = [Line2D([], [], marker="o", ls="", ms=4.6, mfc=SLATE, mec=SLATE, mew=0.9),
         Line2D([], [], marker="o", ls="", ms=4.6, mfc="white", mec=SLATE, mew=0.9)]
    ax.legend(h, ["OptMATH", "NANO-CO"], loc="lower right", bbox_to_anchor=(1.02, 0.99), frameon=False,
              fontsize=7.5, handletextpad=0.1, columnspacing=1.0, ncol=2, borderaxespad=0.0)
    ax.set_title("(a)", loc="left", fontsize=9, pad=4, x=-0.62)

    yb = [3.0, 2.3, 0.9, 0.2]
    for y, (_, lab, n, d) in zip(yb, B):
        left = 0.0
        for c in "DEPBTU":
            if c in d:
                w = 100 * d[c] / n
                bx.barh(y, w, left=left, height=0.5, color=CLS[c], edgecolor="white", linewidth=0.9, zorder=3)
                if w > 1.1:
                    bx.text(left + w / 2, y, c, ha="center", va="center", fontsize=7, color="white" if c in "DU" else INK, zorder=5)
                left += w
        bx.text(left + 0.25, y, f"{left:.1f}", ha="left", va="center", color=INK, fontsize=7.5)
    bx.set_yticks(yb)
    bx.set_yticklabels([b[1] for b in B])
    bx.set_xlim(0, 26)
    bx.set_ylim(-0.3, 3.95)
    bx.set_xticks([0, 5, 10])
    bx.text(0, 3.38, "OptMATH", ha="left", va="bottom", fontsize=8, color=INK)
    bx.text(0, 1.28, "NANO-CO", ha="left", va="bottom", fontsize=8, color=INK)
    bx.set_xlabel("Label misses per 100 certificates", color=INK, x=0.26)
    bx.xaxis.grid(True, color=GRID, lw=0.5, zorder=0)
    bx.set_axisbelow(True)
    for s in ("top", "right", "left"):
        bx.spines[s].set_visible(False)
    bx.spines["bottom"].set_bounds(0, 13.5)
    hh = [plt.Rectangle((0, 0), 1, 1, color=CLS[c]) for c in "DEPBTU"]
    names = [NAMES[c].replace("  ", "\\ \\ " if USE_TEX else "  ") for c in "DEPBTU"]
    bx.legend(hh, names, loc="center right", bbox_to_anchor=(1.07, 0.46), frameon=False, fontsize=7,
              handlelength=0.9, handleheight=0.8, labelspacing=0.35, handletextpad=0.5, borderaxespad=0.0)
    bx.set_title("(b)", loc="left", fontsize=9, pad=4, x=-0.24)
    save(fig, out, "fig1_agreement_audit")
    plt.close(fig)


def fig2(t1, t2, out):
    order = [("stream", "OptMATH-295"), ("confirm", "OptMATH-200"), ("calibration", "NANO-CO-150"), ("heldout", "NANO-CO-95")]
    data = []
    for k, name in order:
        before, after = t2[(k, "panel_base_3of3")], t2[(k, "after check (B or C)")]
        n = int(before["certificates"])
        data_err = sum(int(before["class_" + c]) - int(after["class_" + c]) for c in "DEM")
        withdrawn = n - int(after["certificates"])
        matched_withdrawn = withdrawn - (int(before["label_misses"]) - int(after["label_misses"]))
        correct = CORRECT_FLAGS[k]
        over = matched_withdrawn - correct
        defect = int(after["label_misses"])
        kept_match = n - withdrawn - defect
        data.append((name, n, (kept_match, defect, data_err, correct, over)))
    expect = [("OptMATH-295", 242, (187, 14, 21, 2, 18)), ("OptMATH-200", 163, (131, 12, 6, 4, 10)),
              ("NANO-CO-150", 106, (99, 2, 1, 4, 0)), ("NANO-CO-95", 70, (63, 5, 1, 0, 1))]
    if data != expect:
        fail(f"figure 2 counts differ from the paper: {data}")
    cats = [(2, "withdrawn, data error", "#257de0"), (3, "withdrawn, flag correct", "#9cc4f2"),
            (4, "withdrawn, over-flag", "#ec4647"), (1, "kept, benchmark defect", "#9a9a9a")]
    fig, ax = plt.subplots(figsize=(3.25, 1.55))
    ys = [3, 2, 1, 0]
    for y, (name, n, c) in zip(ys, data):
        left = 0.0
        for i, _, col in cats:
            w = 100 * c[i] / n
            if w == 0:
                continue
            ax.barh(y, w, left=left, height=0.52, color=col, edgecolor="white", linewidth=0.8, zorder=3)
            if w >= 1.6:
                ax.text(left + w / 2, y, f"{w:.0f}", ha="center", va="center", fontsize=7,
                        color="white" if i in (2, 1, 4) else INK, zorder=5)
            left += w
        ax.text(left + 0.5, y, f"{100 * c[0] / n:.0f}{PCT} kept, match the label", ha="left", va="center", fontsize=7, color=SUB)
    ax.set_yticks(ys)
    ax.set_yticklabels([d[0] for d in data])
    ax.set_xlim(0, 38)
    ax.set_ylim(-0.5, 3.5)
    ax.set_xticks([0, 5, 10, 15, 20, 25])
    ax.set_xlabel(f"Three-family certificates ({PCT})", color=INK)
    ax.xaxis.grid(True, color=GRID, lw=0.5, zorder=0)
    ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis="y", length=0)
    h = [plt.Rectangle((0, 0), 1, 1, color=col) for _, _, col in cats]
    fig.legend(h, [lab for _, lab, _ in cats], loc="lower center", bbox_to_anchor=(0.5, -0.33), ncol=2, frameon=False,
               fontsize=7, handlelength=0.9, handleheight=0.8, columnspacing=1.0, labelspacing=0.25)
    save(fig, out, "fig2_verification_outcome")
    plt.close(fig)


if __name__ == "__main__":
    main()
