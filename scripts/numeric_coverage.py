# -*- coding: utf-8 -*-
"""Numeric-coverage check on the extracted specifications (zero token).

Purpose
    A problem text that is not a faithful encoding of the labeled instance
    has one mechanical signature: an extracted base value the text never
    prints. This screens every stream problem for that signature and reports
    flag rates by group.

Method
    For each problem with a stored spec.json, flatten every `base` value and
    test whether it is printed in the problem text. Text numbers are
    tokenized with thousands separators, percentages, attached units,
    negative signs and decimals. A value matches when it is within relative
    tolerance 1e-6 of a text number, or when its exact decimal string occurs.

Flag rules, both reported
    F1  any array parameter with at least 4 entries has coverage below 0.5
    F2  overall coverage below 0.8

Inputs (all required on the command line)
    --runs          <host>/outputs/e1/certify_runs, needs spec.json
                    (private, not distributed)
    --workorder     <host>/outputs/e1/gate_workorder.jsonl, the problem text
                    as the extractor saw it (private, not distributed)
    --admitted      release/reviewer_round/admitted_ids_wild_138.txt (in git)
    --k3            release/k3_attribution.csv (in git)
    --calib-runs    <host>/outputs/e3/certify_runs, control population
                    (private, not distributed)
    --calib-labels  <host>/outputs/e3/e3_labels.jsonl (private, not distributed)
    --out           output directory

Input availability key: "in git" = shipped in this repository; "release
asset" = the v1.0.0 GitHub release asset admitor-v1.0.0-runlogs.zip; "private,
not distributed" = kept by the authors (<host> below is the OptSkills host
clone the experiments ran in).

Reproduce (from the repository root)
    python scripts/numeric_coverage.py --runs <host>/outputs/e1/certify_runs --workorder <host>/outputs/e1/gate_workorder.jsonl --admitted release/reviewer_round/admitted_ids_wild_138.txt --k3 release/k3_attribution.csv --calib-runs <host>/outputs/e3/certify_runs --calib-labels <host>/outputs/e3/e3_labels.jsonl --out reanalysis/reviewer_round

Outputs
    <out>/07_coverage.md, 07_coverage.csv

Paper location
    Section 4.3 (9 / 15 missing-data cases flagged) and Appendix B.1.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys

RELTOL = 1e-6
NUM = re.compile(r"[-+]?\d[\d,]*(?:\.\d+)?(?:[eE][-+]?\d+)?")

try:
    from scipy.stats import fisher_exact
    HAVE = True
except ImportError:
    HAVE = False


def text_numbers(t):
    """Numbers printed in the text, plus percent variants."""
    vals, strs = set(), set()
    for m in NUM.finditer(t or ""):
        s = m.group(0)
        strs.add(s)
        strs.add(s.replace(",", ""))
        try:
            v = float(s.replace(",", ""))
        except ValueError:
            continue
        vals.add(v)
        tail = (t[m.end():m.end() + 1] or "")
        if tail == "%":
            vals.add(v / 100.0)
    return vals, strs


def flat(x):
    if isinstance(x, (list, tuple)):
        for v in x:
            yield from flat(v)
    else:
        yield x


def printed(v, vals, strs):
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return True
    for t in vals:
        if abs(v - t) <= RELTOL * max(1.0, abs(v), abs(t)):
            return True
    for s in (repr(v), str(v), ("%d" % v) if float(v).is_integer() else ""):
        if s and s in strs:
            return True
    return False


def screen(spec, text):
    vals, strs = text_numbers(text)
    total = unmatched = 0
    arrays, f1 = [], False
    for name, e in (spec or {}).items():
        if not isinstance(e, dict):
            continue
        leaves = [x for x in flat(e.get("base")) if isinstance(x, (int, float))
                  and not isinstance(x, bool)]
        if not leaves:
            continue
        hit = sum(1 for v in leaves if printed(v, vals, strs))
        total += len(leaves)
        unmatched += len(leaves) - hit
        cov = hit / len(leaves)
        arrays.append((name, len(leaves), round(cov, 4)))
        if len(leaves) >= 4 and cov < 0.5:
            f1 = True
    overall = (total - unmatched) / total if total else 1.0
    return dict(n_values=total, n_unmatched=unmatched,
                coverage=round(overall, 4), F1=int(f1),
                F2=int(overall < 0.8), arrays=arrays)


def main():
    ap = argparse.ArgumentParser(description="Task 7 numeric coverage screen.")
    for f in ("runs", "workorder", "admitted", "k3", "calib_runs",
              "calib_labels", "out"):
        ap.add_argument("--" + f.replace("_", "-"), dest=f, required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    q = {}
    for line in open(a.workorder, encoding="utf-8"):
        if line.strip():
            r = json.loads(line)
            q[str(r.get("sample_id"))] = r.get("question", "")
    admitted = {l.strip() for l in open(a.admitted, encoding="utf-8") if l.strip()}
    k3 = {r["sample_id"]: r["class"] for r in csv.DictReader(open(a.k3, encoding="utf-8"))}

    rows = []
    for d in sorted(os.listdir(a.runs)):
        p = os.path.join(a.runs, d, "spec.json")
        if not os.path.isfile(p):
            continue
        spec = json.load(open(p, encoding="utf-8")).get("spec")
        s = screen(spec, q.get(d, ""))
        grp = ("wrong" if d in k3 else
               "concordant_admitted" if d in admitted else "other")
        rows.append(dict(sample_id=d, population="stream", group=grp,
                         k3_class=k3.get(d, ""), **{k: v for k, v in s.items()
                                                    if k != "arrays"}))
    # calibration control population
    lab = {}
    for line in open(a.calib_labels, encoding="utf-8"):
        if line.strip():
            r = json.loads(line)
            lab[str(r["sample_id"])] = r.get("question", "")
    for d in sorted(os.listdir(a.calib_runs)):
        p = os.path.join(a.calib_runs, d, "spec.json")
        if not os.path.isfile(p):
            continue
        spec = json.load(open(p, encoding="utf-8")).get("spec")
        s = screen(spec, lab.get(d, ""))
        rows.append(dict(sample_id=d, population="calibration", group="calibration",
                         k3_class="", **{k: v for k, v in s.items() if k != "arrays"}))

    # value-bearing accepts not admitted at 33.3
    notadm = {r["sample_id"] for r in rows
              if r["population"] == "stream" and r["group"] == "other"}

    def block(name, sel):
        n = len(sel)
        f1 = sum(r["F1"] for r in sel)
        f2 = sum(r["F2"] for r in sel)
        cov = sum(r["coverage"] for r in sel) / n if n else float("nan")
        return "| %s | %d | %d (%.1f%%) | %d (%.1f%%) | %.3f |" % (
            name, n, f1, 100.0 * f1 / n if n else 0,
            f2, 100.0 * f2 / n if n else 0, cov)

    stream = [r for r in rows if r["population"] == "stream"]
    wrong = [r for r in stream if r["group"] == "wrong"]
    conc = [r for r in stream if r["group"] == "concordant_admitted"]
    other = [r for r in stream if r["group"] == "other"]
    calib = [r for r in rows if r["population"] == "calibration"]

    L = ["# Task 7. Numeric-coverage screen", "",
         "Zero-token. Generated by `admitor-infra/numeric_coverage.py`.",
         "A base value counts as printed when a text number matches it within "
         "relative tolerance 1e-6, or its exact decimal string occurs. "
         "F1 = any array with >= 4 entries below 0.5 coverage; "
         "F2 = overall coverage below 0.8.", "",
         "## 7.2 Flag rates by group", "",
         "| Group | n | F1 flagged | F2 flagged | mean coverage |",
         "|---|---:|---|---|---:|",
         block("22 round-aware disagreements", wrong),
         block("116 concordant tau-admissions", conc),
         block("value-bearing accepts not admitted at 33.3", other),
         block("calibration specs (control population)", calib), ""]

    L += ["### The 22 disagreements, per case with its K3 class", "",
          "| Problem | class | values | unmatched | coverage | F1 | F2 |",
          "|---|---|---:|---:|---:|---:|---:|"]
    for r in sorted(wrong, key=lambda x: int(x["sample_id"].split("_")[1])):
        L.append("| %s | %s | %d | %d | %.3f | %d | %d |"
                 % (r["sample_id"], r["k3_class"], r["n_values"],
                    r["n_unmatched"], r["coverage"], r["F1"], r["F2"]))
    L.append("")
    for cls in ("d-missing", "d-truncated", "b"):
        sel = [r for r in wrong if r["k3_class"] == cls]
        if sel:
            L.append("- `%s`: n = %d, F1 flagged %d, F2 flagged %d"
                     % (cls, len(sel), sum(r["F1"] for r in sel),
                        sum(r["F2"] for r in sel)))
    L.append("")

    L += ["### 2 x 2 on the 138 tau-admitted problems", ""]
    adm_rows = [r for r in stream if r["group"] in ("wrong", "concordant_admitted")]
    for rule in ("F1", "F2"):
        a11 = sum(1 for r in adm_rows if r["group"] == "wrong" and r[rule])
        a12 = sum(1 for r in adm_rows if r["group"] == "wrong" and not r[rule])
        a21 = sum(1 for r in adm_rows if r["group"] != "wrong" and r[rule])
        a22 = sum(1 for r in adm_rows if r["group"] != "wrong" and not r[rule])
        p = ("%.4f" % fisher_exact([[a11, a12], [a21, a22]])[1] if HAVE else "scipy absent")
        L += ["**%s**: wrong flagged %d / not %d; concordant flagged %d / not %d; "
              "Fisher two-sided p = %s" % (rule, a11, a12, a21, a22, p), ""]

    open(os.path.join(a.out, "07_coverage.md"), "w", encoding="utf-8",
         newline="\n").write("\n".join(L) + "\n")
    keys = ["sample_id", "population", "group", "k3_class", "n_values",
            "n_unmatched", "coverage", "F1", "F2"]
    with open(os.path.join(a.out, "07_coverage.csv"), "w", encoding="utf-8",
              newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows([{k: r[k] for k in keys} for r in rows])
    print("wrote 07_coverage.md and .csv; rows:", len(rows))
    for nm, sel in (("wrong", wrong), ("concordant", conc),
                    ("other", other), ("calibration", calib)):
        print("  %-12s n=%-4d F1=%-4d F2=%-4d meancov=%.3f"
              % (nm, len(sel), sum(r["F1"] for r in sel), sum(r["F2"] for r in sel),
                 sum(r["coverage"] for r in sel) / len(sel) if sel else float("nan")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
