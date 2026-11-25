# -*- coding: utf-8 -*-
"""GateOracle-shaped verdict folders for the judges of a certification run
(zero token).

Purpose
    Reads the stored verdicts of one certify_runs directory and writes, for
    each judge below, one JSON file per problem in the format that
    scripts/e1_relabel.py --arm gate reads ({"sample_id", "decision",
    "clique_value"}). No model and no solver is called.

Judges (one candidate per family; agreement abs(a-b) <= 1e-4*max(1,|a|,|b|))
    gate              the stored verdict of --verdict-file (ACCEPT with a
                      value at the stated instance)
    gate_3fam         gate, three-family cliques only
    gate_tau          gate, accepts whose score 10 x families + clique size
                      + informative instances / 10 is >= --tau (written only
                      when --tau is given)
    panel_base_2of3   any two families agree at the stated instance (two
                      agreeing pairs without a triple certify nothing)
    panel_base_3of3   all three families agree at the stated instance

Inputs
    --runs          a certify_runs directory
    --verdict-file  verdict_full.json (default) or another stored verdict of
                    the same run, e.g. verdict_independent.json
    --out           output directory; one subfolder per judge
    --prefix        optional prefix of the subfolder names
    --tau           optional fitted threshold

Reproduce (from the repository root)
    python scripts/rerun_verdicts.py --runs <runs> --out <out>
"""
from __future__ import annotations

import argparse
import itertools
import json
import os

TOL = 1e-4
ORDER = ["A-direct", "B-structured", "C-direct"]


def close(a, b):
    return abs(a - b) <= TOL * max(1.0, abs(a), abs(b))


def main():
    ap = argparse.ArgumentParser(description="Verdict folders for the judges of a certification run.")
    ap.add_argument("--runs", required=True)
    ap.add_argument("--verdict-file", default="verdict_full.json")
    ap.add_argument("--out", required=True)
    ap.add_argument("--prefix", default="")
    ap.add_argument("--tau", type=float, default=None)
    a = ap.parse_args()

    judges = ["gate", "gate_3fam", "panel_base_2of3", "panel_base_3of3"] + (["gate_tau"] if a.tau is not None else [])
    counts = {j: 0 for j in judges}
    n = 0
    for sid in sorted(os.listdir(a.runs)):
        p = os.path.join(a.runs, sid, a.verdict_file)
        if not os.path.isfile(p):
            continue
        n += 1
        v = json.load(open(p, encoding="utf-8"))
        obj = v.get("objectives") or {}
        bv = {c: float(obj[c][0]) for c in ORDER if isinstance(obj.get(c), list) and obj[c] and obj[c][0] is not None}
        ids = list(bv)
        pairs = [(x, y) for x, y in itertools.combinations(ids, 2) if close(bv[x], bv[y])]
        c2 = c3 = None
        if len(ids) == 3 and len(pairs) == 3:
            c2 = c3 = bv[ids[0]]
        elif len(pairs) == 1:
            c2 = bv[pairs[0][0]]
        val = None
        q, inf, fams = v.get("clique") or [], v.get("informative") or [], v.get("families") or []
        if v.get("decision") == "ACCEPT" and q and 0 in inf:
            series = obj.get(q[0]) or []
            val = series[0] if series else None
        cert = {"gate": val, "gate_3fam": val if len(fams) >= 3 else None,
                "panel_base_2of3": c2, "panel_base_3of3": c3}
        if a.tau is not None:
            score = 10 * len(fams) + len(q) + len(inf) / 10.0
            cert["gate_tau"] = val if score >= a.tau - 1e-9 else None
        for j in judges:
            dj = os.path.join(a.out, a.prefix + j)
            os.makedirs(dj, exist_ok=True)
            x = cert[j]
            counts[j] += x is not None
            with open(os.path.join(dj, sid + ".json"), "w", encoding="utf-8", newline="\n") as fh:
                json.dump({"sample_id": sid, "decision": "ACCEPT" if x is not None else "ABSTAIN",
                           "clique_value": float(x) if x is not None else None}, fh, ensure_ascii=False)
    print(json.dumps({"problems": n, "certificates": counts}))


if __name__ == "__main__":
    main()
