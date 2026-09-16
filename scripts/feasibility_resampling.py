# -*- coding: utf-8 -*-
"""Feasibility-preserving resampling diagnostic (solver only, zero token).

Purpose
    57 of the 62 problems that panel_base_3of3 certifies and the gate did not
    admit were returned UNINFORMATIVE, that is fewer than three instances on
    which two or more candidates produced a finite value. This re-draws the
    resampled instances under a retry rule that rejects a draw no candidate
    can solve, re-solves the stored candidate programs, and runs the clique
    logic unchanged, to measure how much of the coverage loss is attributable
    to the sampler rather than to disagreement.

    Diagnostic only. No admitted set and no downstream number changes.

Retry rule
    m = 5 resampled draws, seed 20260916. A draw is rejected when it is
    infeasible or unbounded for every candidate that returned a finite base
    value; at most 10 attempts per draw. If 10 attempts fail, the last draw
    is kept so the instance count stays at m.

What is and is not modified
    `admitor.consensus.run_l3` is used unmodified. Only the instance generator
    is replaced, by patching `consensus.sample_params` to serve the accepted
    draws in order. The informative rule, the tolerance, the clique search
    and the decision order are untouched.

Inputs
    --runs   <host>/outputs/e1/certify_runs; needs spec.json and the stored
             candidate programs <candidate>.py next to verdict_full.json
             (private, not distributed)
    --ids    release/reviewer_round/11_ids.txt, the 57 ids (in git)
    --vault  datasets/vault/optmath-train-300-labels.jsonl (in git)
    --out    default reanalysis/reviewer_round

Input availability key: "in git" = shipped in this repository; "release
asset" = the v1.0.0 GitHub release asset admitor-v1.0.0-runlogs.zip; "private,
not distributed" = kept by the authors (<host> below is the OptSkills host
clone the experiments ran in).

There is no verification mode that reads stored outputs; reproducing the
numbers re-solves the candidate programs (Pyomo/HiGHS and gurobipy).

Reproduce (from the repository root)
    python scripts/feasibility_resampling.py --runs <host>/outputs/e1/certify_runs

Outputs
    <out>/11_feasibility_resampling.md and .csv

Paper location
    Section 4.2 (8 of 57) and Appendix C.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))  # repository root, for admitor/
from admitor import consensus  # noqa: E402
from admitor.consensus import base_params, run_l3  # noqa: E402
from admitor.generate import make_candidate  # noqa: E402
from score_eval import round_aware, to_num  # noqa: E402

ORDER = ["A-direct", "B-structured", "C-direct"]
FAMILY = {"A-direct": "deepseek", "B-structured": "gpt", "C-direct": "claude"}
STRATEGY = {"A-direct": "direct", "B-structured": "structured", "C-direct": "direct"}
TOL = 1e-4


def close(a, b):
    return abs(a - b) <= TOL * max(1.0, abs(a), abs(b))


def main():
    ap = argparse.ArgumentParser(description="Task 11 feasibility resampling.")
    ap.add_argument("--runs", required=True)
    ap.add_argument("--ids", default="release/reviewer_round/11_ids.txt")
    ap.add_argument("--vault", default="datasets/vault/optmath-train-300-labels.jsonl")
    ap.add_argument("--out", default="reanalysis/reviewer_round")
    ap.add_argument("--m", type=int, default=5)
    ap.add_argument("--max-attempts", type=int, default=10)
    ap.add_argument("--seed", type=int, default=20260916)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--timeout", type=int, default=60)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    vault = {}
    for line in open(a.vault, encoding="utf-8"):
        if line.strip():
            r = json.loads(line)
            vault["sample_%s" % r["idx"]] = str(r.get("answer"))

    ids = [l.strip() for l in open(a.ids, encoding="utf-8") if l.strip()]
    if a.limit:
        ids = ids[: a.limit]

    rows = []
    t_start = time.time()
    for n, sid in enumerate(ids, 1):
        d = os.path.join(a.runs, sid)
        try:
            spec = json.load(open(os.path.join(d, "spec.json"), encoding="utf-8"))["spec"]
            vf = json.load(open(os.path.join(d, "verdict_full.json"), encoding="utf-8"))
        except Exception as e:
            rows.append(dict(sample_id=sid, status="load_error:%s" % type(e).__name__))
            continue

        objs = vf.get("objectives") or {}
        bases = {}
        for c in ORDER:
            s = objs.get(c)
            if isinstance(s, list) and s and s[0] is not None:
                bases[c] = float(s[0])
        cands = []
        for c in ORDER:
            f = os.path.join(d, c + ".py")
            if os.path.isfile(f):
                code = open(f, encoding="utf-8").read()
                cands.append(make_candidate(code, c, FAMILY[c], STRATEGY[c],
                                            timeout=a.timeout))
        if len(cands) < 2 or not bases:
            rows.append(dict(sample_id=sid, status="insufficient_stored_programs"))
            continue

        solvers = [c for c in cands if c.id in bases]
        rng = random.Random(a.seed)
        accepted, attempts_used = [], []
        for _k in range(a.m):
            draw = None
            for att in range(1, a.max_attempts + 1):
                cand_draw = consensus.sample_params(spec, rng)
                alive = False
                for c in solvers:
                    try:
                        r = c.solve(cand_draw)
                    except Exception:
                        continue
                    if r.status == "optimal" and r.objective is not None:
                        alive = True
                        break
                draw = cand_draw
                if alive:
                    attempts_used.append(att)
                    break
            else:
                attempts_used.append(a.max_attempts)
            accepted.append(draw)

        # serve the accepted draws through the unmodified run_l3
        orig = consensus.sample_params
        queue = list(accepted)

        def served(_spec, _rng, _q=queue):
            return _q.pop(0) if _q else orig(_spec, _rng)

        consensus.sample_params = served
        try:
            v = run_l3(cands, spec, m=a.m, seed=a.seed)
        finally:
            consensus.sample_params = orig

        cert = None
        if v.decision == "ACCEPT" and v.clique:
            series = v.objectives.get(v.clique[0]) or []
            cert = series[0] if series else None
        base_unan = bases[ORDER[0]] if len(bases) == 3 and all(
            close(bases[x], bases[y]) for x in bases for y in bases) else None
        ans = vault.get(sid)
        rows.append(dict(
            sample_id=sid, status="ok",
            n_informative=len(v.informative),
            reaches_three=len(v.informative) >= 3,
            decision=v.decision,
            n_families=len(v.families),
            certificate=cert,
            base_unanimous=base_unan,
            cert_equals_base=(None if cert is None or base_unan is None
                              else bool(close(float(cert), base_unan))),
            vault=ans,
            cert_correct=(None if cert is None or ans is None
                          else bool(round_aware(to_num(cert), to_num(ans), ans))),
            mean_attempts=round(sum(attempts_used) / len(attempts_used), 2),
        ))
        print("  [%d/%d] %s informative=%d %s cert=%s (%.0fs elapsed)"
              % (n, len(ids), sid, len(v.informative), v.decision, cert,
                 time.time() - t_start), flush=True)

    ok = [r for r in rows if r.get("status") == "ok"]
    L = ["# Task 11. Feasibility-preserving resampling diagnostic", "",
         "Solver only, zero token. Generated by "
         "`admitor-infra/feasibility_resampling.py`.",
         "`run_l3` is unmodified; only the instance generator is replaced. "
         "Diagnostic only: no admitted set and no downstream number changes.", "",
         "Retry rule: m = %d, seed %d, at most %d attempts per draw; a draw is "
         "rejected when no candidate that solved the stated instance can solve it."
         % (a.m, a.seed, a.max_attempts), "",
         "| Quantity | Value |", "|---|---:|",
         "| problems attempted | %d |" % len(rows),
         "| problems re-run successfully | %d |" % len(ok),
         "| reaching three informative instances | %d |"
         % sum(1 for r in ok if r["reaches_three"]),
         "| verdict ACCEPT | %d |" % sum(1 for r in ok if r["decision"] == "ACCEPT"),
         "| verdict ABSTAIN | %d |" % sum(1 for r in ok if r["decision"] == "ABSTAIN"),
         "| verdict UNINFORMATIVE | %d |"
         % sum(1 for r in ok if r["decision"] == "UNINFORMATIVE"),
         "| certificate equals the base-unanimous value | %d |"
         % sum(1 for r in ok if r["cert_equals_base"]),
         "| certificate correct against the vault | %d |"
         % sum(1 for r in ok if r["cert_correct"]),
         "| certificate wrong against the vault | %d |"
         % sum(1 for r in ok if r["cert_correct"] is False), "",
         "## Per problem", "",
         "| Problem | informative | decision | families | certificate | "
         "= base value | vault correct | mean attempts |",
         "|---|---:|---|---:|---|---|---|---:|"]
    for r in ok:
        L.append("| %s | %d | %s | %d | %s | %s | %s | %s |"
                 % (r["sample_id"], r["n_informative"], r["decision"],
                    r["n_families"], r["certificate"], r["cert_equals_base"],
                    r["cert_correct"], r["mean_attempts"]))
    bad = [r for r in rows if r.get("status") != "ok"]
    if bad:
        L += ["", "Not re-run: " + ", ".join("%s (%s)" % (r["sample_id"], r["status"])
                                             for r in bad), ""]
    open(os.path.join(a.out, "11_feasibility_resampling.md"), "w",
         encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
    if rows:
        keys = sorted({k for r in rows for k in r})
        with open(os.path.join(a.out, "11_feasibility_resampling.csv"), "w",
                  encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=keys)
            w.writeheader()
            w.writerows(rows)
    print("wrote 11_feasibility_resampling.md and .csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
