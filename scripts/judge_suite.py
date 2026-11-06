# -*- coding: utf-8 -*-
"""Judge suite on the stored E1 stream records (zero token).

Purpose
    Every judge below is computed from the stored per-instance objective
    values of the three panel candidates (artifacts/e1/certify_runs, in git).
    No model and no solver is called. For each judge the script writes
    GateOracle-shaped verdicts (one JSON file per problem, the format written
    by panel_base_judges.py), so that the unchanged scripts
    e1_relabel.py --arm gate and candidate_crosstab.py produce the
    candidate-level row of each judge exactly as for Table 3.

Judges
    Reference rows (reconciliation gates against Table 3):
        panel_base_2of3, panel_base_3of3, gate_asdeployed, gate_tau
    One family at the stated instance theta0:
        single_deepseek, single_gpt, single_claude
    Two families at theta0:
        pair0_deepseek_gpt, pair0_deepseek_claude, pair0_gpt_claude
    Two families with resampling (Step 3 restricted to the pair, m=5,
    min_informative=3):
        pairR_deepseek_gpt, pairR_deepseek_claude, pairR_gpt_claude
    Number of resampled instances m = 2, 3, 4 (instances 0..m of the stored
    draws, which are exactly the draws run_l3 makes with that m because the
    sampler draws instances sequentially from one seeded generator):
        gate_m2, gate_m3, gate_m4, gate3_m2, gate3_m3, gate3_m4
    min_informative = 1, 2 (m = 5):
        gate_mi1, gate_mi2, gate3_mi1, gate3_mi2
    Decomposition of the stated-instance judges by the gate's outcome:
        base2_kept, base2_lost_uninformative, base2_lost_failure,
        base2_lost_divergence, base3_kept, base3_lost_uninformative,
        base3_lost_shrink, base3_lost_divergence
    gate3_* keeps three-family accepts only, which is the set selected by the
    fitted threshold tau = 33.3 (score = 10 x families + clique size +
    informative instances / 10, one candidate per family).

Rules, verbatim from admitor/consensus.py run_l3
    agreement      abs(a - b) <= 1e-4 * max(1, |a|, |b|)
    informative    an instance on which >= 2 of the candidates in the judge
                   return a value
    UNINFORMATIVE  fewer than min_informative informative instances
    ACCEPT         maximum clique over the informative instances spans >= 2
                   families; certificate = the clique's value at theta0, and
                   only when theta0 is informative
    The stated-instance judges reproduce panel_base_judges.py, including its
    chain rule (two agreeing pairs without a triple emit no certificate).

Inputs (all in git)
    --runs   artifacts/e1/certify_runs
    --vault  datasets/vault/optmath-train-300-labels.jsonl
    --out    default outputs/additional_2026-11

Outputs
    <out>/verdicts/<judge>/<sample_id>.json
    <out>/problem_level.csv, <out>/problem_level.md, <out>/stream_facts.json

Reconciliation gate
    Every judge's problem-level (certified, wrong) pair must equal EXPECTED
    below, computed independently before this script was written. Any
    difference prints STOP and the script exits with code 2.

Reproduce (from the repository root)
    python scripts/judge_suite.py
"""
from __future__ import annotations

import argparse
import csv
import itertools
import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from score_eval import round_aware, to_num  # noqa: E402

TOL = 1e-4
DEV = {"sample_%d" % i for i in (1, 2, 3, 4, 5)}
ORDER = ["A-direct", "B-structured", "C-direct"]
FAM = {"A-direct": "deepseek", "B-structured": "gpt", "C-direct": "claude"}
ID = {v: k for k, v in FAM.items()}

EXPECTED = {
    "panel_base_2of3": (245, 38), "panel_base_3of3": (200, 26),
    "gate_asdeployed": (170, 29), "gate_tau": (138, 22),
    "single_deepseek": (240, 40), "single_gpt": (226, 35), "single_claude": (261, 48),
    "pair0_deepseek_gpt": (205, 29), "pair0_deepseek_claude": (228, 33), "pair0_gpt_claude": (212, 28),
    "pairR_deepseek_gpt": (140, 23), "pairR_deepseek_claude": (158, 26), "pairR_gpt_claude": (148, 24),
    "gate_m2": (152, 25), "gate_m3": (164, 29), "gate_m4": (170, 29),
    "gate3_m2": (123, 18), "gate3_m3": (133, 22), "gate3_m4": (138, 22),
    "gate_mi1": (238, 35), "gate_mi2": (178, 30), "gate3_mi1": (194, 26), "gate3_mi2": (144, 23),
    "base2_kept": (170, 29), "base2_lost_uninformative": (68, 6),
    "base2_lost_failure": (1, 0), "base2_lost_divergence": (6, 3),
    "base3_kept": (138, 22), "base3_lost_uninformative": (57, 4),
    "base3_lost_shrink": (4, 0), "base3_lost_divergence": (1, 0),
}


def cost(j):
    """(model calls, solver runs) per problem: extraction + generations, candidates x instances."""
    if j.startswith("single_"):
        return "1 + 1", 1
    if j.startswith("pair0_"):
        return "1 + 2", 2
    if j.startswith("panel_base"):
        return "1 + 3", 3
    if j.startswith("pairR_"):
        return "1 + 2", 12
    if j.startswith(("gate_mi", "gate3_mi")):
        return "1 + 3", 18
    if j.startswith(("gate_m", "gate3_m")):
        return "1 + 3", 3 * (int(j[-1]) + 1)
    return "1 + 3", 18


def close(a, b):
    return abs(a - b) <= TOL * max(1.0, abs(a), abs(b))


def max_clique(ids, edge):
    for k in range(len(ids), 0, -1):
        for combo in itertools.combinations(ids, k):
            if all(edge(a, b) for a, b in itertools.combinations(combo, 2)):
                return list(combo)
    return []


def decide(objs, ids, m=5, min_inf=3):
    """run_l3's decision on stored values, candidates ids, instances 0..m."""
    o = {i: objs[i][: m + 1] for i in ids}
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
    """(cert_2of3, cert_3of3, agreeing group) exactly as panel_base_judges.py."""
    ids = [c for c in ORDER if c in bv]
    pairs = [(x, y) for x, y in itertools.combinations(ids, 2) if close(bv[x], bv[y])]
    if len(ids) == 3 and len(pairs) == 3:
        return bv[ids[0]], bv[ids[0]], list(ids)
    if len(pairs) == 1:
        x, y = pairs[0]
        return bv[x], None, [x, y]
    return None, None, None


def main():
    ap = argparse.ArgumentParser(description="Judge suite on the stored E1 stream records (zero token).")
    ap.add_argument("--runs", default="artifacts/e1/certify_runs")
    ap.add_argument("--vault", default="datasets/vault/optmath-train-300-labels.jsonl")
    ap.add_argument("--out", default="outputs/additional_2026-11")
    a = ap.parse_args()

    vault = {}
    for line in open(a.vault, encoding="utf-8"):
        if line.strip():
            r = json.loads(line)
            vault["sample_%s" % r["idx"]] = str(r.get("answer"))
    runs = {}
    for d in sorted(os.listdir(a.runs), key=lambda s: int(s.split("_")[1])):
        p = os.path.join(a.runs, d, "verdict_full.json")
        if os.path.isfile(p):
            runs[d] = json.load(open(p, encoding="utf-8"))
    if len(runs) != 298:
        print("STOP: expected 298 certify runs, found %d" % len(runs)); sys.exit(2)

    cert = {j: {} for j in EXPECTED}          # judge -> sid -> value or None
    fate2, fate3 = {}, {}
    for sid, v in runs.items():
        obj = v["objectives"]
        bv = base_values(v)
        c2, c3, grp = panel_judgements(bv)
        cert["panel_base_2of3"][sid] = c2
        cert["panel_base_3of3"][sid] = c3
        d, q, inf, val = decide(obj, ORDER)
        if (d, q, inf) != (v["decision"], v["clique"], v["informative"]):
            print("STOP: re-derivation differs from the stored verdict for %s" % sid); sys.exit(2)
        cert["gate_asdeployed"][sid] = val
        cert["gate_tau"][sid] = val if len(q) == 3 else None
        for f in ("deepseek", "gpt", "claude"):
            cert["single_" + f][sid] = bv.get(ID[f])
        for f1, f2 in itertools.combinations(("deepseek", "gpt", "claude"), 2):
            x, y = ID[f1], ID[f2]
            cert["pair0_%s_%s" % (f1, f2)][sid] = bv[x] if (x in bv and y in bv and close(bv[x], bv[y])) else None
            cert["pairR_%s_%s" % (f1, f2)][sid] = decide(obj, [x, y])[3]
        for m in (2, 3, 4):
            dm, qm, _, vm = decide(obj, ORDER, m=m)
            cert["gate_m%d" % m][sid] = vm
            cert["gate3_m%d" % m][sid] = vm if len(qm) == 3 else None
        for k in (1, 2):
            dk, qk, _, vk = decide(obj, ORDER, min_inf=k)
            cert["gate_mi%d" % k][sid] = vk
            cert["gate3_mi%d" % k][sid] = vk if len(qk) == 3 else None
        # decomposition of the stated-instance judges by the gate's outcome
        for need, base_val, fate, pref in ((2, c2, fate2, "base2"), (3, c3, fate3, "base3")):
            for t in ("kept", "lost_uninformative", "lost_failure", "lost_divergence", "lost_shrink"):
                if pref + "_" + t in cert:
                    cert[pref + "_" + t][sid] = None
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
            fate[sid] = t
            cert[pref + "_" + t][sid] = base_val

    # write GateOracle-shaped verdicts
    for j, per in cert.items():
        dj = os.path.join(a.out, "verdicts", j)
        os.makedirs(dj, exist_ok=True)
        for sid in runs:
            val = per.get(sid)
            doc = {"sample_id": sid, "decision": "ACCEPT" if val is not None else "ABSTAIN",
                   "clique_value": float(val) if val is not None else None}
            with open(os.path.join(dj, sid + ".json"), "w", encoding="utf-8", newline="\n") as fh:
                json.dump(doc, fh, ensure_ascii=False)

    # problem-level accuracy, non-dev, round-aware against the vault
    rows, stop = [], False
    for j, per in cert.items():
        n = k = 0
        for sid, val in per.items():
            if sid in DEV or val is None:
                continue
            n += 1
            ans = vault[sid]
            k += not round_aware(to_num(val), to_num(ans), ans)
        exp = EXPECTED[j]
        status = "PASS" if (n, k) == exp else "FAIL expected %s" % (exp,)
        if (n, k) != exp:
            stop = True
        calls, solves = cost(j)
        rows.append(dict(judge=j, model_calls=calls, solver_runs=solves, certified=n,
                         wrong=k, false_pct=round(100.0 * k / n, 1) if n else "", gate=status))
    with open(os.path.join(a.out, "problem_level.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    md = ["| Judge | Model calls | Solver runs | Certified | Wrong | False % | Gate |",
          "|---|---|---:|---:|---:|---:|---|"]
    md += ["| `%s` | %s | %s | %d | %d | %s | %s |" % (r["judge"], r["model_calls"], r["solver_runs"],
           r["certified"], r["wrong"], r["false_pct"], r["gate"]) for r in rows]

    # stream facts
    nd = {s: v for s, v in runs.items() if s not in DEV}
    nvals = Counter(sum(1 for c in ORDER if v["objectives"][c][0] is not None) for v in nd.values())
    none_status = Counter(v["statuses"][c][0].split(":")[0] for v in nd.values()
                          if all(v["objectives"][x][0] is None for x in ORDER) for c in ORDER)
    const = {"as_deployed": [0, 0], "three_family": [0, 0]}
    for s, v in nd.items():
        if v["decision"] != "ACCEPT" or 0 not in v["informative"]:
            continue
        vals = [v["objectives"][v["clique"][0]][k] for k in v["informative"]]
        flag = 0 if all(close(vals[0], x) for x in vals) else 1
        const["as_deployed"][flag] += 1
        if len(v["clique"]) == 3:
            const["three_family"][flag] += 1
    div_cases = sorted((s for s, t in fate2.items() if t == "lost_divergence"), key=lambda s: int(s.split("_")[1]))
    facts = {
        "theta0_values_count_nondev": {str(k): nvals[k] for k in sorted(nvals)},
        "theta0_statuses_when_no_value": dict(none_status),
        "certified_value_constant_vs_varies": const,
        "base2_divergence_cases": [{"sample_id": s, "base_value": cert["panel_base_2of3"][s],
                                    "label": vault[s],
                                    "base_value_correct": round_aware(to_num(cert["panel_base_2of3"][s]),
                                                                      to_num(vault[s]), vault[s])}
                                   for s in div_cases],
    }
    json.dump(facts, open(os.path.join(a.out, "stream_facts.json"), "w", encoding="utf-8"), indent=1)
    md += ["", "Stream facts: " + json.dumps(facts)]
    open(os.path.join(a.out, "problem_level.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    print("\n".join(md))
    if stop:
        print("\nSTOP: at least one judge differs from EXPECTED; do not continue.")
        sys.exit(2)
    print("\nALL GATES PASS")


if __name__ == "__main__":
    main()
