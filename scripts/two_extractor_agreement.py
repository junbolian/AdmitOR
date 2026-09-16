# -*- coding: utf-8 -*-
"""Two-extractor preliminary: extractor agreement at four levels (zero token).

Three extractors: the pilot (`deepseek-v3.2`, stored in
`certify_runs/<sid>/spec.json`), `claude-sonnet-4-6` and `gpt-5.4`.

Levels, each reported separately
    L1  raw key-name set equality.
    L2  value-signature alignment: a bijection between the two parameter sets
        matching on shape and on base values within the scoring tolerance,
        irrespective of key names. The pair agrees when every parameter of
        each specification has a match in the other.
    L3  elementwise base-value agreement under the L2 bijection.
    L4  perturbation-domain compatibility under that bijection, after the
        guardrails: same mode, and for abs mode overlapping [lo, hi].

Also reported: the number of cases in which the pilot aligns at L2 with both
other extractors (three-way alignment), and an exploratory, not preregistered,
decomposition of each pair into (a) unmatched parameters, (b) shape-matched
parameters with conflicting values and (c) agreeing parameters, per group and
in total.

Inputs
    --cases        release/reviewer_round/09_cases.csv (in git)
    --extractions  release/reviewer_round/09_extractions (in git)
    --runs         <host>/outputs/e1/certify_runs, needs the pilot spec.json
                   (private, not distributed)
    --workorder    <host>/outputs/e1/gate_workorder.jsonl, the problem text
                   (private, not distributed)
    --out          default reanalysis/reviewer_round

Input availability key: "in git" = shipped in this repository; "release
asset" = the v1.0.0 GitHub release asset admitor-v1.0.0-runlogs.zip; "private,
not distributed" = kept by the authors (<host> below is the OptSkills host
clone the experiments ran in).

Reproduce (from the repository root)
    python scripts/two_extractor_agreement.py --runs <host>/outputs/e1/certify_runs --workorder <host>/outputs/e1/gate_workorder.jsonl

Outputs
    <out>/09_two_extractor.md, 09_two_extractor.csv

Paper location
    Section 4.3 (22/22, 21/22 vs 18/22) and Appendix B.1 Table 4.
"""
from __future__ import annotations

import argparse
import csv
import itertools
import json
import os
import re
import sys

TOL = 1e-4
PILOT = "deepseek-v3.2 (pilot)"
FAMS = [PILOT, "claude-sonnet-4-6", "gpt-5.4"]

try:
    from scipy.stats import fisher_exact
    HAVE = True
except ImportError:
    HAVE = False

NUM = re.compile(r"-?\d[\d,]*\.?\d*")


def text_numbers(t):
    out = set()
    for m in NUM.finditer(t or ""):
        try:
            out.add(float(m.group(0).replace(",", "")))
        except ValueError:
            pass
    return out


def flat(x):
    if isinstance(x, (list, tuple)):
        for v in x:
            yield from flat(v)
    else:
        yield x


def shape(x):
    if isinstance(x, (list, tuple)):
        return (len(x),) + (shape(x[0]) if x else ())
    return ()


def close(a, b):
    try:
        a, b = float(a), float(b)
    except (TypeError, ValueError):
        return a == b
    return abs(a - b) <= TOL * max(1.0, abs(a), abs(b))


def params_of(spec):
    return {k: v for k, v in (spec or {}).items() if isinstance(v, dict)}


def values(p):
    return [x for x in flat(p.get("base")) if isinstance(x, (int, float))]


def align(A, B):
    """Greedy bijection on (shape, approximate values). Returns pairs or None."""
    used, pairs = set(), []
    for ka, pa in A.items():
        sa, va = shape(pa.get("base")), values(pa)
        best = None
        for kb, pb in B.items():
            if kb in used:
                continue
            if shape(pb.get("base")) != sa:
                continue
            vb = values(pb)
            if len(va) != len(vb):
                continue
            if all(close(x, y) for x, y in zip(va, vb)):
                best = kb
                break
        if best is None:
            return None
        used.add(best)
        pairs.append((ka, best))
    if len(used) != len(B):
        return None
    return pairs


def levels(A, B):
    l1 = set(A) == set(B)
    pairs = align(A, B)
    l2 = pairs is not None
    l3 = l4 = False
    if l2:
        l3 = all(len(values(A[a])) == len(values(B[b]))
                 and all(close(x, y) for x, y in zip(values(A[a]), values(B[b])))
                 for a, b in pairs)
        ok = True
        for a, b in pairs:
            pa = (A[a].get("perturb") or {})
            pb = (B[b].get("perturb") or {})
            ma, mb = str(pa.get("mode", "")).lower(), str(pb.get("mode", "")).lower()
            if ma != mb:
                ok = False
                break
            if ma == "abs":
                la, ha = pa.get("lo"), pa.get("hi")
                lb, hb = pb.get("lo"), pb.get("hi")
                if None in (la, ha, lb, hb) or max(la, lb) > min(ha, hb):
                    ok = False
                    break
        l4 = ok
    return {"L1": l1, "L2": l2, "L3": l3, "L4": l4}


def decompose(A, B):
    """Split one pair's parameters into (a) unmatched, (b) shape-matched but
    value-conflicting, (c) shape- and value-matched. Also counts unmatched
    array parameters with at least 4 base entries. Exploratory, not a
    preregistered rule; greedy in A's key order like align()."""
    usedB, a, b, c = set(), 0, 0, 0
    big_unmatched = 0
    for ka, pa in A.items():
        sa, va = shape(pa.get("base")), values(pa)
        exact = shapeonly = None
        for kb, pb in B.items():
            if kb in usedB or shape(pb.get("base")) != sa:
                continue
            vb = values(pb)
            if len(va) == len(vb) and all(close(x, y) for x, y in zip(va, vb)):
                exact = kb
                break
            if shapeonly is None:
                shapeonly = kb
        if exact is not None:
            usedB.add(exact)
            c += 1
        elif shapeonly is not None:
            usedB.add(shapeonly)
            b += 1
        else:
            a += 1
            if len(va) >= 4:
                big_unmatched += 1
    a += len(B) - len(usedB)     # parameters of B with no counterpart in A
    return a, b, c, big_unmatched


def main():
    ap = argparse.ArgumentParser(description="Task 9 agreement analysis.")
    ap.add_argument("--cases", default="release/reviewer_round/09_cases.csv")
    ap.add_argument("--extractions", default="release/reviewer_round/09_extractions")
    ap.add_argument("--runs", required=True)
    ap.add_argument("--workorder", required=True)
    ap.add_argument("--out", default="reanalysis/reviewer_round")
    a = ap.parse_args()

    q = {}
    for line in open(a.workorder, encoding="utf-8"):
        if line.strip():
            r = json.loads(line)
            q[str(r.get("sample_id"))] = r.get("question", "")

    cases = list(csv.DictReader(open(a.cases, encoding="utf-8")))
    rows = []
    PAIRS = [(PILOT, "claude-sonnet-4-6", "P-C"), (PILOT, "gpt-5.4", "P-G"),
             ("claude-sonnet-4-6", "gpt-5.4", "C-G")]
    GROUPS = ("class (d)", "label error", "control")
    decomp, bigcases, threeway = {}, {}, 0
    for c in cases:
        sid = c["sample_id"]
        specs = {}
        p = os.path.join(a.runs, sid, "spec.json")
        if os.path.isfile(p):
            specs[PILOT] = params_of(json.load(open(p, encoding="utf-8")).get("spec"))
        for fam in FAMS[1:]:
            f = os.path.join(a.extractions, fam, sid + ".json")
            if os.path.isfile(f):
                d = json.load(open(f, encoding="utf-8"))
                if "error" not in d:
                    specs[fam] = params_of(d.get("spec"))
        if len(specs) < 2:
            continue
        rec = dict(sample_id=sid, group=c["group"], k3_class=c["k3_class"],
                   score=c["score"], n_extractors=len(specs))
        for x, y in itertools.combinations(FAMS, 2):
            if x in specs and y in specs:
                lv = levels(specs[x], specs[y])
                tag = ("P-C" if y == "claude-sonnet-4-6" and x == PILOT else
                       "P-G" if y == "gpt-5.4" and x == PILOT else "C-G")
                for k, v in lv.items():
                    rec["%s_%s" % (tag, k)] = int(v)
        # values absent from the text on which all extractors agree
        tn = text_numbers(q.get(sid, ""))
        unprinted_agreed = 0
        if len(specs) == 3:
            pr = align(specs[PILOT], specs["claude-sonnet-4-6"])
            pg = align(specs[PILOT], specs["gpt-5.4"])
            if pr and pg:
                threeway += 1
                for k, pa in specs[PILOT].items():
                    for v in values(pa):
                        if not any(close(v, t) for t in tn):
                            unprinted_agreed += 1
        rec["unprinted_values_agreed_by_all_three"] = unprinted_agreed
        rows.append(rec)
        grp = ("label error" if c["k3_class"] == "b"
               else "class (d)" if c["k3_class"] else "control")
        any_big = False
        for x, y, tag in PAIRS:
            if x not in specs or y not in specs:
                continue
            ua, vb_, ag, big = decompose(specs[x], specs[y])
            s = decomp.setdefault((grp, tag), [0, 0, 0])
            s[0] += ua
            s[1] += vb_
            s[2] += ag
            any_big = any_big or big > 0
        bigcases[grp] = bigcases.get(grp, 0) + int(any_big)

    def any_dis(r, tags, lvl):
        vals = [r.get("%s_%s" % (t, lvl)) for t in tags]
        vals = [v for v in vals if v is not None]
        return 0 if not vals else int(any(v == 0 for v in vals))

    L = ["# Task 9. Two- and three-extractor agreement", "",
         "Zero-token analysis of the extractions produced by Task 9.2.",
         "Extractors: pilot `deepseek-v3.2` (stored), `claude-sonnet-4-6`, `gpt-5.4`.",
         "scipy available: %s." % HAVE, "",
         "## Spend", "",
         "88 calls, 0 errors, 156,594 tokens "
         "(Claude 83,067; GPT 73,527). Every response returned its own model name.", "",
         "## Case groups", "",
         "| Group | n | score 33.3 | 33.4 | 33.5 | 33.6 |", "|---|---:|---:|---:|---:|---:|"]
    for g in ("wrong", "control"):
        rs = [r for r in rows if r["group"] == g]
        L.append("| %s | %d | %d | %d | %d | %d |"
                 % (g, len(rs),
                    sum(1 for r in rs if r["score"] == "33.3"),
                    sum(1 for r in rs if r["score"] == "33.4"),
                    sum(1 for r in rs if r["score"] == "33.5"),
                    sum(1 for r in rs if r["score"] == "33.6")))
    L.append("")

    for label, tags in (("E = 2 (pilot and Claude)", ["P-C"]),
                        ("E = 3 (all three pairs)", ["P-C", "P-G", "C-G"])):
        L += ["## %s" % label, "",
              "| Level | class (d) + label error: any disagreement | control: any disagreement | "
              "Fisher p (two-sided) |", "|---|---|---|---|"]
        for lvl in ("L1", "L2", "L3", "L4"):
            w = [r for r in rows if r["group"] == "wrong"]
            c = [r for r in rows if r["group"] == "control"]
            wd = sum(any_dis(r, tags, lvl) for r in w)
            cd = sum(any_dis(r, tags, lvl) for r in c)
            p = ("%.4f" % fisher_exact([[wd, len(w) - wd], [cd, len(c) - cd]])[1]
                 if HAVE else "scipy absent")
            L.append("| %s | %d / %d | %d / %d | %s |"
                     % (lvl, wd, len(w), cd, len(c), p))
        L.append("")

    tr = [r for r in rows if r["k3_class"] == "d-truncated"]
    L += ["## The five truncated-precision cases, reported separately", "",
          "| Level | any disagreement among the 5 (E = 3) |", "|---|---|"]
    for lvl in ("L1", "L2", "L3", "L4"):
        L.append("| %s | %d / %d |"
                 % (lvl, sum(any_dis(r, ["P-C", "P-G", "C-G"], lvl) for r in tr), len(tr)))
    L += ["",
          "## Values the problem text does not print, on which all three extractors agree", "",
          "| Group | cases | total such values |", "|---|---:|---:|"]
    for g in ("wrong", "control"):
        rs = [r for r in rows if r["group"] == g]
        L.append("| %s | %d | %d |"
                 % (g, sum(1 for r in rs if r["unprinted_values_agreed_by_all_three"]),
                    sum(r["unprinted_values_agreed_by_all_three"] for r in rs)))
    L.append("")
    L += ["Three-way alignment (the pilot aligned at L2 with both other extractors), "
          "required for the statistic above: %d of %d cases." % (threeway, len(rows)), ""]

    L += ["## Exploratory decomposition, not a preregistered rule", "",
          "Each pair's L2 outcome split into (a) parameters in one specification with no",
          "shape-and-value match in the other, (b) shape-matched parameters whose values",
          "conflict, and (c) shape-matched parameters whose values agree.", "",
          "| Group | Pair | (a) unmatched | (b) shape match, value conflict | (c) agreeing |",
          "|---|---|---:|---:|---:|"]
    for grp in GROUPS:
        for _x, _y, tag in PAIRS:
            s = decomp.get((grp, tag))
            if s:
                L.append("| %s | %s | %d | %d | %d |" % (grp, tag, s[0], s[1], s[2]))
    L += ["", "Totals per group:", "", "| Group | (a) | (b) | (c) |", "|---|---:|---:|---:|"]
    grand = [0, 0, 0]
    for grp in GROUPS:
        t = [0, 0, 0]
        for _x, _y, tag in PAIRS:
            for i, v in enumerate(decomp.get((grp, tag), [0, 0, 0])):
                t[i] += v
        grand = [g + v for g, v in zip(grand, t)]
        L.append("| %s | %d | %d | %d |" % (grp, t[0], t[1], t[2]))
    L.append("| all groups | %d | %d | %d |" % tuple(grand))
    L += ["", "Cases in which an array parameter with at least 4 entries in one",
          "specification has no value-matched counterpart in another:", "",
          "| Group | cases |", "|---|---:|"]
    for grp in GROUPS:
        L.append("| %s | %d |" % (grp, bigcases.get(grp, 0)))
    L.append("")

    open(os.path.join(a.out, "09_two_extractor.md"), "w",
         encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
    keys = sorted({k for r in rows for k in r})
    with open(os.path.join(a.out, "09_two_extractor.csv"), "w",
              encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    print("wrote 09_two_extractor.md and .csv; cases analysed:", len(rows))
    for lvl in ("L1", "L2", "L3", "L4"):
        wr = [r for r in rows if r["group"] == "wrong"]
        cr = [r for r in rows if r["group"] == "control"]
        print("  %s  wrong %d/%d  control %d/%d"
              % (lvl, sum(any_dis(r, ["P-C", "P-G", "C-G"], lvl) for r in wr), len(wr),
                 sum(any_dis(r, ["P-C", "P-G", "C-G"], lvl) for r in cr), len(cr)))
    print("  three-way alignment %d of %d; unmatched %d, value conflicts %d, agreeing %d"
          % (threeway, len(rows), grand[0], grand[1], grand[2]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
