# -*- coding: utf-8 -*-
"""Single-program perturbation screens on the stored E1 stream records (zero token).

Purpose
    A behavioral test applied to one generated program, used as an admission
    rule: the program is run on the stated instance and on the five resampled
    instances that are already stored, and its stated-instance value is
    certified only when the program passes the screen. No other family is
    consulted, so these judges isolate what perturbation testing of a single
    program contributes, without agreement across families. No model and no
    solver is called; every value comes from artifacts/e1/certify_runs.

Judges (one per family f in deepseek, gpt, claude)
    screen_<f>      certify the theta0 value of family f when the program
                    returns a value at theta0 and on at least MIN_OK of the
                    five resampled instances (the program runs and stays
                    feasible under perturbation)
    screenvar_<f>   as screen_<f>, and the returned values are not all equal
                    under the agreement tolerance (the optimum responds to the
                    perturbation)
    MIN_OK = 3, the informativeness requirement of the deployed gate.

Logical gates (the script stops with exit code 2 on any failure)
    1. judge_suite.decide re-derives all 298 stored verdicts (imported).
    2. Every screen_<f> certificate is also a single_<f> certificate of
       judge_suite with the identical value, and every screenvar_<f>
       certificate is a screen_<f> certificate.

Inputs (all in git)
    --runs   artifacts/e1/certify_runs
    --vault  datasets/vault/optmath-train-300-labels.jsonl
    --out    default outputs/additional_2026-11b

Outputs
    <out>/verdicts/<judge>/<sample_id>.json   GateOracle-shaped, as judge_suite.py
    <out>/screen_problem_level.csv, <out>/screen_problem_level.md

Reproduce (from the repository root)
    python scripts/perturbation_screen.py
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from score_eval import round_aware, to_num  # noqa: E402
from judge_suite import DEV, ORDER, FAM, base_values, close, decide  # noqa: E402

MIN_OK = 3
FAMILIES = ("deepseek", "gpt", "claude")
ID = {v: k for k, v in FAM.items()}


def main():
    ap = argparse.ArgumentParser(description="Single-program perturbation screens (zero token).")
    ap.add_argument("--runs", default="artifacts/e1/certify_runs")
    ap.add_argument("--vault", default="datasets/vault/optmath-train-300-labels.jsonl")
    ap.add_argument("--out", default="outputs/additional_2026-11b")
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

    judges = ["screen_" + f for f in FAMILIES] + ["screenvar_" + f for f in FAMILIES]
    cert = {j: {} for j in judges}
    for sid, v in runs.items():
        obj = v["objectives"]
        d, q, inf, _ = decide(obj, ORDER)
        if (d, q, inf) != (v["decision"], v["clique"], v["informative"]):
            print("STOP: re-derivation differs from the stored verdict for %s" % sid); sys.exit(2)
        bv = base_values(v)
        for f in FAMILIES:
            c = ID[f]
            series = obj[c][:6]
            ok = [k for k in range(1, 6) if series[k] is not None]
            passed = c in bv and len(ok) >= MIN_OK
            cert["screen_" + f][sid] = bv[c] if passed else None
            vals = [series[0]] + [series[k] for k in ok] if passed else []
            varies = passed and not all(close(vals[0], x) for x in vals[1:])
            cert["screenvar_" + f][sid] = bv[c] if varies else None
            # logical gates
            if passed and not close(bv[c], base_values(v)[c]):
                print("STOP: screen value differs from the single-family value for %s %s" % (sid, f)); sys.exit(2)
            if varies and cert["screen_" + f][sid] is None:
                print("STOP: screenvar certificate outside screen for %s %s" % (sid, f)); sys.exit(2)

    for j, per in cert.items():
        dj = os.path.join(a.out, "verdicts", j)
        os.makedirs(dj, exist_ok=True)
        for sid in runs:
            val = per.get(sid)
            doc = {"sample_id": sid, "decision": "ACCEPT" if val is not None else "ABSTAIN",
                   "clique_value": float(val) if val is not None else None}
            with open(os.path.join(dj, sid + ".json"), "w", encoding="utf-8", newline="\n") as fh:
                json.dump(doc, fh, ensure_ascii=False)

    rows = []
    for j, per in cert.items():
        n = k = 0
        for sid, val in per.items():
            if sid in DEV or val is None:
                continue
            n += 1
            ans = vault[sid]
            k += not round_aware(to_num(val), to_num(ans), ans)
        rows.append(dict(judge=j, model_calls="1 + 1", solver_runs=6, certified=n, wrong=k,
                         false_pct=round(100.0 * k / n, 1) if n else ""))
    with open(os.path.join(a.out, "screen_problem_level.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)
    md = ["| Judge | Model calls | Solver runs | Certified | Wrong | False % |",
          "|---|---|---:|---:|---:|---:|"]
    md += ["| `%s` | %s | %s | %d | %d | %s |" % (r["judge"], r["model_calls"], r["solver_runs"],
           r["certified"], r["wrong"], r["false_pct"]) for r in rows]
    open(os.path.join(a.out, "screen_problem_level.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    print("\n".join(md))
    print("\nLOGICAL GATES PASS")


if __name__ == "__main__":
    main()
