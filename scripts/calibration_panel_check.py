# -*- coding: utf-8 -*-
"""Agreement at the stated instance against the resampled comparison, on the
calibration set (zero token).

Purpose
    The calibration set (NANO-CO, solver-verified answers) is certified by
    the same three-family panel as the training stream, but its problems are
    disjoint from the stream and its answers are correct by construction, so
    it contains no text or label errors. This script asks, on that set,
    whether the comparison of resampled values removes wrong values that
    agreement at the stated instance theta0 would certify, at matched
    coverage. Every judge is computed from the stored per-instance objective
    values. No model and no solver is called.

Judges (same definitions as scripts/judge_suite.py on the stream)
    single_<f>          one family's value at theta0
    pair0_<f1>_<f2>     two given families agree at theta0
    panel_base_2of3     any two families agree at theta0 (chain rule as in
                        panel_base_judges.py)
    panel_base_3of3     all three families agree at theta0
    gate_asdeployed     stored gate decision, m = 5, min_informative = 3
    gate_mi1, gate_mi2  gate with min_informative = 1, 2
    gate_tau            three-family accepts of the gate (the threshold
                        tau = 33.3 was fitted on this set: in-sample)
    gate3_mi1           three-family accepts with min_informative = 1
    base_exactly_two    exactly two families agree at theta0 (the band that
                        the fitted threshold excludes, before resampling)
    gate_two            the gate's two-family accepts (score 22.x)
    base2_* / base3_*   fate of each panel_base certificate under the gate:
                        kept, lost_uninformative, lost_failure,
                        lost_divergence, lost_shrink

Grading
    label_match of scripts/e3_calibrate.py (the ruler that produced
    artifacts/e3/calibration.json): 2-decimal half-up match or absolute gap
    <= 0.005. A certificate is a value at theta0; an ACCEPT whose clique has
    no value at theta0 certifies nothing and is counted in
    accept_without_theta0_value.

Inputs
    --runs    <host>/outputs/e3/certify_runs   (private; <sid>/verdict_full.json)
    --labels  <host>/outputs/e3/e3_labels.jsonl (private)
    --nano    datasets/train_set/nano-co.jsonl   (public; cross-check of labels)
    --calib   artifacts/e3/calibration.json      (public; reconciliation)
    --out     default outputs/additional_2026-11d

Reconciliation gates (any failure prints STOP and exits with code 2)
    G1  every run with a label re-derives its stored (decision, clique,
        informative) under decide(m=5, min_inf=3);
    G2  the ACCEPT runs split into true and false cliques exactly as the
        positive and null records of calibration.json (same sample ids),
        using e3_calibrate.py's own certified_value and label_match;
    G3  every label equals the answer of the matching nano-co.jsonl row
        (sample id e3_<problem_type>_<index>).

Outputs
    <out>/calib_problem_level.csv, <out>/calib_problem_level.md,
    <out>/calib_withheld.csv (one row per value that the comparison withholds),
    <out>/calib_facts.json

Reproduce (from the repository root)
    python scripts/calibration_panel_check.py --runs <host>/outputs/e3/certify_runs --labels <host>/outputs/e3/e3_labels.jsonl
"""
from __future__ import annotations

import argparse
import csv
import itertools
import json
import math
import os
import sys
from decimal import ROUND_HALF_UP, Decimal

TOL = 1e-4
ORDER = ["A-direct", "B-structured", "C-direct"]
FAM = {"A-direct": "deepseek", "B-structured": "gpt", "C-direct": "claude"}
ID = {v: k for k, v in FAM.items()}


# ---- rules, verbatim from scripts/judge_suite.py (admitor/consensus.py run_l3) ----
def close(a, b):
    return abs(a - b) <= TOL * max(1.0, abs(a), abs(b))


def max_clique(ids, edge):
    for k in range(len(ids), 0, -1):
        for combo in itertools.combinations(ids, k):
            if all(edge(a, b) for a, b in itertools.combinations(combo, 2)):
                return list(combo)
    return []


def decide(objs, ids, m=5, min_inf=3):
    o = {i: (list(objs[i]) + [None] * (m + 1))[: m + 1] for i in ids}
    inf = [k for k in range(m + 1) if sum(1 for i in ids if o[i][k] is not None) >= 2]
    if len(inf) < min_inf:
        return "UNINFORMATIVE", [], inf, None
    edge = lambda a, b: all(o[a][k] is not None and o[b][k] is not None
                            and close(o[a][k], o[b][k]) for k in inf)
    q = max_clique(ids, edge)
    if len(q) >= 2:
        val = o[q[0]][0] if 0 in inf else None
        return "ACCEPT", q, inf, val
    return "ABSTAIN", [], inf, None


def base_values(v):
    out = {}
    for c in ORDER:
        s = (v.get("objectives") or {}).get(c)
        if isinstance(s, list) and s and s[0] is not None:
            out[c] = float(s[0])
    return out


def panel_judgements(bv):
    ids = [c for c in ORDER if c in bv]
    pairs = [(x, y) for x, y in itertools.combinations(ids, 2) if close(bv[x], bv[y])]
    if len(ids) == 3 and len(pairs) == 3:
        return bv[ids[0]], bv[ids[0]], list(ids)
    if len(pairs) == 1:
        x, y = pairs[0]
        return bv[x], None, [x, y]
    return None, None, None


# ---- grading, verbatim from scripts/e3_calibrate.py ----
def label_match(certified, answer):
    try:
        c = float(certified)
        a = float(str(answer).strip())
    except (TypeError, ValueError):
        return False
    q = Decimal("0.01")
    try:
        if Decimal(repr(c)).quantize(q, rounding=ROUND_HALF_UP) == Decimal(repr(a)).quantize(q, rounding=ROUND_HALF_UP):
            return True
    except Exception:
        pass
    return abs(c - a) <= 0.005


def certified_value(v):
    obj = v.get("objectives") or {}
    clique = v.get("clique") or []
    if not clique:
        return None
    vals = obj.get(clique[0]) or []
    return vals[0] if vals else None


def fisher_greater(a, b, c, d):
    """One-sided Fisher exact p that the first row has the larger wrong share.
    Table [[a wrong, b right] withheld, [c wrong, d right] kept]."""
    n1, n2, k = a + b, c + d, a + c
    N = n1 + n2
    denom = math.comb(N, k)
    return sum(math.comb(n1, x) * math.comb(n2, k - x) for x in range(a, min(n1, k) + 1)) / denom


def main():
    ap = argparse.ArgumentParser(description="Calibration-set check of the resampled comparison (zero token).")
    ap.add_argument("--runs", required=True)
    ap.add_argument("--labels", required=True)
    ap.add_argument("--nano", default="datasets/train_set/nano-co.jsonl")
    ap.add_argument("--calib", default="artifacts/e3/calibration.json")
    ap.add_argument("--out", default="outputs/additional_2026-11d")
    a = ap.parse_args()

    labels = {}
    for line in open(a.labels, encoding="utf-8"):
        if line.strip():
            r = json.loads(line)
            labels[r["sample_id"]] = r
    runs = {}
    for sid in sorted(os.listdir(a.runs)):
        p = os.path.join(a.runs, sid, "verdict_full.json")
        if os.path.isfile(p) and sid in labels:
            runs[sid] = json.load(open(p, encoding="utf-8"))
    print("labels: %d, runs with a label: %d" % (len(labels), len(runs)))

    # G3: labels agree with the public NANO-CO answers
    nano = {}
    for line in open(a.nano, encoding="utf-8"):
        if line.strip():
            r = json.loads(line)
            nano["e3_%s_%s" % (r.get("problem_type"), r.get("index"))] = r.get("answer")
    bad = [s for s in labels if s not in nano or str(nano[s]).strip() != str(labels[s]["answer"]).strip()]
    if bad:
        print("STOP G3: %d labels differ from nano-co.jsonl, e.g. %s" % (len(bad), bad[:5])); sys.exit(2)

    # G1: re-derivation of the stored verdicts
    for sid, v in runs.items():
        d, q, inf, _ = decide(v["objectives"], ORDER)
        if (d, q, inf) != (v["decision"], v["clique"], v["informative"]):
            print("STOP G1: re-derivation differs from the stored verdict for %s: %s vs %s"
                  % (sid, (d, q, inf), (v["decision"], v["clique"], v["informative"]))); sys.exit(2)

    # G2: true and false cliques as in calibration.json
    cal = json.load(open(a.calib, encoding="utf-8"))
    pos_ref = {r["sample_id"] for r in cal["records"]["positive"]}
    null_ref = {r["sample_id"] for r in cal["records"]["null"]}
    pos = {s for s, v in runs.items() if v.get("decision") == "ACCEPT" and label_match(certified_value(v), labels[s]["answer"])}
    null = {s for s, v in runs.items() if v.get("decision") == "ACCEPT" and not label_match(certified_value(v), labels[s]["answer"])}
    if pos != pos_ref or null != null_ref:
        print("STOP G2: positive %d vs %d, null %d vs %d; differing ids %s"
              % (len(pos), len(pos_ref), len(null), len(null_ref), sorted((pos ^ pos_ref) | (null ^ null_ref))[:10])); sys.exit(2)
    print("RECONCILIATION PASSED (G1, G2, G3)")

    judges = ["single_deepseek", "single_gpt", "single_claude",
              "pair0_deepseek_gpt", "pair0_deepseek_claude", "pair0_gpt_claude",
              "panel_base_2of3", "panel_base_3of3",
              "base_exactly_two", "gate_two",
              "gate_asdeployed", "gate_mi1", "gate_mi2", "gate_tau", "gate3_mi1",
              "base2_kept", "base2_lost_uninformative", "base2_lost_failure", "base2_lost_divergence",
              "base3_kept", "base3_lost_uninformative", "base3_lost_failure", "base3_lost_divergence", "base3_lost_shrink"]
    cert = {j: {} for j in judges}
    withheld_rows = []
    accept_no_theta0 = []
    for sid, v in runs.items():
        obj = v["objectives"]
        bv = base_values(v)
        c2, c3, grp = panel_judgements(bv)
        cert["panel_base_2of3"][sid] = c2
        cert["panel_base_3of3"][sid] = c3
        d, q, inf, val = decide(obj, ORDER)
        if d == "ACCEPT" and val is None:
            accept_no_theta0.append(sid)
        cert["gate_asdeployed"][sid] = val
        cert["gate_tau"][sid] = val if len(q) == 3 else None
        cert["gate_two"][sid] = val if len(q) == 2 else None
        cert["base_exactly_two"][sid] = c2 if (c2 is not None and c3 is None) else None
        for f in ("deepseek", "gpt", "claude"):
            cert["single_" + f][sid] = bv.get(ID[f])
        for f1, f2 in itertools.combinations(("deepseek", "gpt", "claude"), 2):
            x, y = ID[f1], ID[f2]
            cert["pair0_%s_%s" % (f1, f2)][sid] = bv[x] if (x in bv and y in bv and close(bv[x], bv[y])) else None
        for k in (1, 2):
            _, qk, _, vk = decide(obj, ORDER, min_inf=k)
            cert["gate_mi%d" % k][sid] = vk
            if k == 1:
                cert["gate3_mi1"][sid] = vk if len(qk) == 3 else None
        for need, base_val, pref in ((2, c2, "base2"), (3, c3, "base3")):
            for j in judges:
                if j.startswith(pref + "_"):
                    cert[j][sid] = None
            if base_val is None:
                continue
            g = grp if need == 2 else ORDER
            if d == "UNINFORMATIVE":
                t = "lost_uninformative"
            elif d == "ABSTAIN":
                rs = [k for k in inf if k > 0]
                div = any(obj[x][k] is not None and obj[y][k] is not None and not close(obj[x][k], obj[y][k])
                          for x, y in itertools.combinations(g, 2) for k in rs)
                t = "lost_divergence" if div else "lost_failure"
            elif len(q) < need:
                t = "lost_shrink"
            else:
                t = "kept"
            if pref + "_" + t in cert:
                cert[pref + "_" + t][sid] = base_val
            if t != "kept":
                withheld_rows.append(dict(sample_id=sid, level=pref, fate=t, theta0_value=base_val,
                                          label=labels[sid]["answer"],
                                          wrong=not label_match(base_val, labels[sid]["answer"]),
                                          gate_decision=d, clique=";".join(q), informative=len(inf)))

    n_total = len(runs)
    rows = []
    for j in judges:
        n = k = 0
        for sid, val in cert[j].items():
            if val is None:
                continue
            n += 1
            k += not label_match(val, labels[sid]["answer"])
        rows.append(dict(judge=j, certified=n, wrong=k, correct=n - k,
                         false_pct=round(100.0 * k / n, 1) if n else "",
                         coverage_pct=round(100.0 * n / n_total, 1)))

    def get(j):
        return next(r for r in rows if r["judge"] == j)

    null_no_theta0 = sorted(s for s in null if certified_value(runs[s]) is None)
    facts = dict(problems=n_total, accepts=len(pos) + len(null), true_cliques=len(pos), false_cliques=len(null),
                 false_cliques_without_theta0_value=null_no_theta0,
                 accept_without_theta0_value=len(accept_no_theta0), accept_without_theta0_ids=accept_no_theta0,
                 decisions=dict(sorted(__import__("collections").Counter(v["decision"] for v in runs.values()).items())),
                 values_at_theta0=dict(sorted(__import__("collections").Counter(
                     sum(1 for c in ORDER if base_values(v).get(c) is not None) for v in runs.values()).items())))
    # the comparison's removals against what it keeps, two-family level and three-family level
    for pref, base in (("base2", "panel_base_2of3"), ("base3", "panel_base_3of3")):
        kept = get(pref + "_kept")
        div = get(pref + "_lost_divergence")
        facts[pref] = dict(base=get(base), kept=kept, lost_divergence=div,
                           lost_uninformative=get(pref + "_lost_uninformative"),
                           lost_failure=get(pref + "_lost_failure"))
        if div["certified"]:
            facts[pref]["fisher_one_sided_p_divergence_vs_kept"] = fisher_greater(
                div["wrong"], div["correct"], kept["wrong"], kept["correct"])
    # matched-coverage comparison: min_informative = 1 isolates the comparison
    facts["matched"] = dict(panel_base_2of3=get("panel_base_2of3"), gate_mi1=get("gate_mi1"),
                            panel_base_3of3=get("panel_base_3of3"), gate3_mi1=get("gate3_mi1"))

    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "calib_problem_level.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    md = ["| Judge | Certified | Wrong | Correct | False % | Coverage % |", "|---|---:|---:|---:|---:|---:|"]
    md += ["| `%s` | %d | %d | %d | %s | %s |" % (r["judge"], r["certified"], r["wrong"], r["correct"],
                                                  r["false_pct"], r["coverage_pct"]) for r in rows]
    open(os.path.join(a.out, "calib_problem_level.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    if withheld_rows:
        with open(os.path.join(a.out, "calib_withheld.csv"), "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(withheld_rows[0])); w.writeheader(); w.writerows(withheld_rows)
    json.dump(facts, open(os.path.join(a.out, "calib_facts.json"), "w", encoding="utf-8"), indent=2, default=str)
    print("\n".join(md))
    print(json.dumps(facts, indent=2, default=str))


if __name__ == "__main__":
    main()
