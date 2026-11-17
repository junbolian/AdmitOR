# -*- coding: utf-8 -*-
"""Resampling restricted to parameters whose perturbation keeps the programs
solvable (solver only, zero token).

Purpose
    scripts/redraw_suite.py showed that rejecting and redrawing whole
    instances does not remove the coverage loss: on about one third of the
    draws no program can be made solvable in ten attempts. This script tests
    a sampler that chooses WHICH parameters to perturb instead. A parameter
    is perturbed alone, with every other parameter at its stated value, and
    it is kept only if the programs stay solvable. The resampled instances
    then perturb the kept parameters jointly and leave the others at their
    stated values. Parameters that enter only the objective never change the
    feasible region, so they always pass; programs with different feasible
    regions still return different optimal values when the costs change.

Parameter test (label-free; uses only whether a program returns a value)
    For each parameter with a base value that is not an indicator structure,
    K_TEST = 2 single-parameter draws are made with the domain-restricted
    sampler of redraw_suite.sample_domain (seed 43). The candidates that
    returned a value at theta0 are solved on each.
        safe_all   every such candidate returns a value on every test draw
        safe_two   at least two such candidates return a value on every
                   test draw
    A problem's tests stop after TEST_BUDGET_S seconds; parameters not
    reached are treated as not safe and counted in `untested`.

Variants (m = 5, seed 42; decision rule unchanged, imported from
redraw_suite.py)
    orig          copied from the results of redraw_suite.py (--prev), whose
                  gate G1 already matched it to the stored runs
    pscreen_all   joint domain-restricted draws over the safe_all parameters
    pscreen_two   joint domain-restricted draws over the safe_two parameters
    When a problem has no safe parameter, no resampled instance is formed:
    its resampled cells hold no value (status "unperturbed"), so the gate
    with min_informative = 3 returns UNINFORMATIVE for it.

Inputs
    --runs, --set, --labels   as for redraw_suite.py
    --prev   <redraw out>/results.jsonl of the same set
    --out    e.g. outputs/redraw_2026-11/stream_param

Modes
    run        appends one JSON line per problem to <out>/results.jsonl;
               resumable; --ids reruns the listed problems (last line wins)
    summarize  runs redraw_suite's summarize on the three variants (gates G1,
               G2, G3; tables; stream verdict folders) and adds
               <out>/param_facts.json

Reproduce (from the repository root)
    python scripts/param_redraw.py run --set stream --runs <host>/outputs/e1/certify_runs --labels datasets/vault/optmath-train-300-labels.jsonl --prev outputs/redraw_2026-11/stream/results.jsonl --out outputs/redraw_2026-11/stream_param --workers 8
    python scripts/param_redraw.py summarize --set stream --runs <host>/outputs/e1/certify_runs --labels datasets/vault/optmath-train-300-labels.jsonl --prev outputs/redraw_2026-11/stream/results.jsonl --out outputs/redraw_2026-11/stream_param
"""
from __future__ import annotations

import argparse
import json
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
import redraw_suite as rs  # noqa: E402

K_TEST = 2
TEST_SEED = 43
TEST_BUDGET_S = 900
PVARS = ["orig", "pscreen_all", "pscreen_two"]


def run_problem(args):
    runs, sid, timeout, prev = args
    t0 = time.time()
    d = os.path.join(runs, sid)
    try:
        from admitor import consensus
        from admitor.generate import make_candidate
        spec = json.load(open(os.path.join(d, "spec.json"), encoding="utf-8"))["spec"]
        cands = []
        for c in rs.ORDER:
            f = os.path.join(d, c + ".py")
            if os.path.isfile(f):
                cands.append(make_candidate(open(f, encoding="utf-8").read(), c, rs.FAMILY[c], rs.STRATEGY[c], timeout=timeout))
        bp = consensus.base_params(spec)
        if not cands or bp is None:
            return dict(sample_id=sid, status="no_programs_or_base")
        po = prev["variants"]["orig"]
        base_row = {c.id: (po["objectives"][c.id][0], po["statuses"][c.id][0]) for c in cands}
        alive = [c for c in cands if base_row[c.id][0] is not None]

        names = [n for n, s in spec.items() if "base" in s and not rs.domain_of(s["base"])[0]]
        safe_all, safe_two, untested, tests = [], [], [], {}
        rng_t = random.Random(TEST_SEED)
        if len(alive) >= 2:
            for n in names:
                if time.time() - t0 > TEST_BUDGET_S:
                    untested.append(n)
                    continue
                counts = []
                for _ in range(K_TEST):
                    p = dict(bp)
                    p[n] = rs.sample_domain({n: spec[n]}, rng_t)[n]
                    row = rs.solve_all(alive, p)
                    counts.append(sum(1 for c in alive if row[c.id][0] is not None))
                tests[n] = counts
                if all(k == len(alive) for k in counts):
                    safe_all.append(n)
                if all(k >= 2 for k in counts):
                    safe_two.append(n)

        res = dict(sample_id=sid, status="ok", candidates=[c.id for c in cands],
                   n_params=len(spec), n_indicator=prev.get("n_indicator", 0), n_nonneg=prev.get("n_nonneg", 0),
                   n_testable=len(names), n_alive=len(alive), safe_all=safe_all, safe_two=safe_two,
                   untested=untested, tests=tests, variants={"orig": po})
        for var, safe in (("pscreen_all", safe_all), ("pscreen_two", safe_two)):
            rows = [base_row]
            rng = random.Random(rs.SEED)
            sub = {n: spec[n] for n in safe}
            for _k in range(rs.M):
                if not safe:
                    rows.append({c.id: (None, "unperturbed") for c in cands})
                    continue
                draw = dict(bp)
                draw.update(rs.sample_domain(sub, rng))
                rows.append(rs.solve_all(cands, draw))
            res["variants"][var] = dict(
                objectives={c.id: [r[c.id][0] for r in rows] for c in cands},
                statuses={c.id: [r[c.id][1] for r in rows] for c in cands},
                attempts=[1] * rs.M, draws_out_of_domain=0)
        res["seconds"] = round(time.time() - t0, 1)
        return res
    except Exception as e:
        return dict(sample_id=sid, status="error:%s:%s" % (type(e).__name__, str(e)[:200]))


def cmd_run(a):
    os.makedirs(a.out, exist_ok=True)
    path = os.path.join(a.out, "results.jsonl")
    prev = rs.read_results(a.prev)
    done = rs.read_results(path)
    ids = rs.list_ids(a.runs)
    lack = [s for s in ids if s not in prev or prev[s].get("status") != "ok"]
    if lack:
        print("STOP: --prev has no ok result for %d problems, e.g. %s" % (len(lack), lack[:5])); sys.exit(2)
    if a.ids:
        todo = [l.strip() for l in open(a.ids, encoding="utf-8") if l.strip()]
    else:
        todo = [s for s in ids if s not in done or done[s].get("status") != "ok"]
    if a.limit:
        todo = todo[: a.limit]
    print("problems: %d, already done: %d, to run: %d" % (len(ids), len(done), len(todo)), flush=True)
    jobs = [(a.runs, s, a.timeout, prev[s]) for s in todo]
    t0 = time.time()
    with open(path, "a", encoding="utf-8") as fh:
        def sink(n, r):
            fh.write(json.dumps(r) + "\n"); fh.flush()
            print("  [%d/%d] %s %s %ss safe_all=%s/%s (%.0fs elapsed)"
                  % (n, len(jobs), r["sample_id"], r["status"], r.get("seconds", "-"),
                     len(r.get("safe_all", [])), r.get("n_testable", "-"), time.time() - t0), flush=True)
        if a.workers <= 1:
            for n, j in enumerate(jobs, 1):
                sink(n, run_problem(j))
        else:
            from concurrent.futures import ProcessPoolExecutor, as_completed
            with ProcessPoolExecutor(max_workers=a.workers) as ex:
                futs = [ex.submit(run_problem, j) for j in jobs]
                for n, f in enumerate(as_completed(futs), 1):
                    sink(n, f.result())
    print("done")


def cmd_summarize(a):
    rs.VARIANTS = list(PVARS)
    rs.cmd_summarize(a)
    res = rs.read_results(os.path.join(a.out, "results.jsonl"))
    ids = rs.list_ids(a.runs)
    two = [s for s in ids if res[s]["n_alive"] >= 2]
    facts = dict(set=a.set, problems=len(ids), problems_with_two_values_at_theta0=len(two),
                 testable_parameters=sum(res[s]["n_testable"] for s in two),
                 untested_parameters=sum(len(res[s]["untested"]) for s in two), variants={})
    for var, key in (("pscreen_all", "safe_all"), ("pscreen_two", "safe_two")):
        moved = fixed = 0
        for s in two:
            o = res[s]["variants"][var]["objectives"]
            cids = [c for c in rs.ORDER if c in o]
            d, q, inf, val = rs.decide(o, cids)
            if d == "ACCEPT" and val is not None:
                vals = [o[q[0]][k] for k in inf]
                if all(rs.close(vals[0], x) for x in vals[1:]):
                    fixed += 1
                else:
                    moved += 1
        facts["variants"][var] = dict(
            safe_parameters=sum(len(res[s][key]) for s in two),
            problems_without_safe_parameter=sum(1 for s in two if not res[s][key]),
            problems_all_parameters_safe=sum(1 for s in two if res[s]["n_testable"] and len(res[s][key]) == res[s]["n_testable"]),
            certificates_value_changes_across_instances=moved,
            certificates_value_constant_across_instances=fixed)
    facts["solve_seconds_total"] = round(sum(res[s].get("seconds", 0) for s in ids), 1)
    json.dump(facts, open(os.path.join(a.out, "param_facts.json"), "w", encoding="utf-8"), indent=2)
    print(json.dumps(facts, indent=2))


def main():
    ap = argparse.ArgumentParser(description="Resampling over solvability-preserving parameters (solver only).")
    ap.add_argument("mode", choices=["run", "summarize"])
    ap.add_argument("--set", required=True, choices=["stream", "calib"])
    ap.add_argument("--runs", required=True)
    ap.add_argument("--labels", required=True)
    ap.add_argument("--prev", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--timeout", type=int, default=60)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--ids", default="")
    a = ap.parse_args()
    (cmd_run if a.mode == "run" else cmd_summarize)(a)


if __name__ == "__main__":
    main()
