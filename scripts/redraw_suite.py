# -*- coding: utf-8 -*-
"""Resampling with domain-restricted and solvability-screened draws (solver
only, zero token).

Purpose
    The gate's coverage loss comes from resampled instances that no candidate
    can solve, and some of its abstentions come from draws outside the value
    domain of the stated data (for example an entry of -1 in a matrix of 0/1
    preferences). This script re-draws the resampled instances of every
    stored certification run under four alternative samplers, re-solves the
    stored candidate programs on them, and applies the gate's decision rule
    unchanged. It measures how coverage and the error rate of the
    certificates change with the sampler. No model is called.

Variants (m = 5 resampled draws, seed 42, the seed of the stored runs)
    orig            the sampler of admitor.consensus.sample_params. It must
                    reproduce the stored objective values (gate G1).
    screen1         orig, and a draw is rejected and redrawn (at most
                    MAX_ATTEMPTS attempts) unless at least one candidate that
                    returned a value at theta0 returns a value on it. This is
                    the retry rule of scripts/feasibility_resampling.py.
    domain          draws restricted to the value domain of the stated data,
                    read from the base values of the specification alone:
                    (a) a list-valued parameter whose base entries are all 0
                        or 1 (at least two entries) is an indicator structure
                        and is kept at its base value in every draw;
                    (b) a parameter whose base entries are all >= 0 is never
                        drawn below 0 (an absolute range [lo, hi] becomes
                        [max(lo, 0), max(hi, 0)]; relative perturbation of a
                        non-negative base is already non-negative).
                    Everything else is sampled as in orig.
    domain_screen1  domain with the screen1 retry rule.
    domain_screen2  domain, and a draw is accepted only when at least two
                    candidates return a value on it.

    The screens use only whether a program returns a value, never the value
    and never a label. Every candidate is solved once per attempted draw and
    the result is cached, so the decision uses the same solves as the screen.

Decision rule
    decide() below is the rule of admitor/consensus.py run_l3, verbatim from
    scripts/judge_suite.py: agreement abs(a-b) <= 1e-4*max(1,|a|,|b|); an
    instance is informative when >= 2 candidates return a value; ACCEPT when
    the maximum clique over the informative instances has >= 2 members.

Inputs
    --runs    a certify_runs directory with, per problem, verdict_full.json,
              spec.json and the stored programs A-direct.py, B-structured.py,
              C-direct.py (<host>/outputs/e1/certify_runs for the stream,
              <host>/outputs/e3/certify_runs for the calibration set)
    --set     stream | calib (chooses the grading ruler and the labels)
    --labels  stream: datasets/vault/optmath-train-300-labels.jsonl
              calib:  <host>/outputs/e3/e3_labels.jsonl
    --out     output directory of this set, e.g. outputs/redraw_2026-11/stream

Modes
    run        solve; appends one JSON line per problem to <out>/results.jsonl
               and skips problems already present (resumable). With --ids, the
               listed problems are solved again and their new line replaces
               the old one when the file is read (last line wins).
    summarize  reads <out>/results.jsonl; runs the gates; writes the tables
               and, for the stream, GateOracle-shaped verdict folders for
               scripts/e1_relabel.py and scripts/candidate_crosstab.py.

Gates (summarize; any failure prints STOP and exits with code 2)
    G1  variant orig reproduces, for every problem, the stored decision,
        clique and informative set, and every stored objective value
        (None in the same cells, values within the agreement tolerance).
    G2  the stated-instance judges are identical across variants (theta0 is
        never redrawn).
    G3  results exist for every problem of the runs directory.

Outputs (summarize)
    <out>/redraw_problem_level.csv and .md   one row per variant and judge
    <out>/redraw_facts.json                  draws, attempts, domain counts
    <out>/redraw_per_problem.csv             one row per problem and variant
    <out>/verdicts/<variant>__<judge>/<sample_id>.json   (stream only)

Reproduce (from the repository root)
    python scripts/redraw_suite.py run --set stream --runs <host>/outputs/e1/certify_runs --labels datasets/vault/optmath-train-300-labels.jsonl --out outputs/redraw_2026-11/stream --workers 6
    python scripts/redraw_suite.py summarize --set stream --runs <host>/outputs/e1/certify_runs --labels datasets/vault/optmath-train-300-labels.jsonl --out outputs/redraw_2026-11/stream
"""
from __future__ import annotations

import argparse
import csv
import itertools
import json
import os
import random
import sys
import time
from collections import Counter
from decimal import ROUND_HALF_UP, Decimal

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))  # repository root, for admitor/

TOL = 1e-4
M = 5
SEED = 42
MAX_ATTEMPTS = 10
ORDER = ["A-direct", "B-structured", "C-direct"]
FAMILY = {"A-direct": "deepseek", "B-structured": "gpt", "C-direct": "claude"}
STRATEGY = {"A-direct": "direct", "B-structured": "structured", "C-direct": "direct"}
VARIANTS = ["orig", "screen1", "domain", "domain_screen1", "domain_screen2"]
DEV = {"sample_%d" % i for i in (1, 2, 3, 4, 5)}


# ---- decision rule, verbatim from scripts/judge_suite.py ----
def close(a, b):
    return abs(a - b) <= TOL * max(1.0, abs(a), abs(b))


def max_clique(ids, edge):
    for k in range(len(ids), 0, -1):
        for combo in itertools.combinations(ids, k):
            if all(edge(a, b) for a, b in itertools.combinations(combo, 2)):
                return list(combo)
    return []


def decide(objs, ids, m=M, min_inf=3):
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


def panel_judgements(bv):
    ids = [c for c in ORDER if c in bv]
    pairs = [(x, y) for x, y in itertools.combinations(ids, 2) if close(bv[x], bv[y])]
    if len(ids) == 3 and len(pairs) == 3:
        return bv[ids[0]], bv[ids[0]], list(ids)
    if len(pairs) == 1:
        x, y = pairs[0]
        return bv[x], None, [x, y]
    return None, None, None


# ---- grading ----
def label_match(certified, answer):  # verbatim from scripts/e3_calibrate.py
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


def load_labels(kind, path):
    lab = {}
    for line in open(path, encoding="utf-8"):
        if not line.strip():
            continue
        r = json.loads(line)
        if kind == "stream":
            lab["sample_%s" % r["idx"]] = str(r.get("answer"))
        else:
            lab[r["sample_id"]] = str(r.get("answer"))
    return lab


def make_grader(kind):
    if kind == "stream":
        from score_eval import round_aware, to_num
        return lambda val, ans: bool(round_aware(to_num(val), to_num(ans), ans))
    return lambda val, ans: label_match(val, ans)


# ---- value domain of the stated data ----
def flat(x):
    if isinstance(x, (list, tuple)):
        for y in x:
            yield from flat(y)
    else:
        yield x


def numeric_entries(base):
    out = []
    for v in flat(base):
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            return None
        out.append(float(v))
    return out


def domain_of(base):
    """(is_indicator, is_nonneg) from the base value alone."""
    ent = numeric_entries(base)
    if not ent:
        return False, False
    indicator = isinstance(base, (list, tuple)) and len(ent) >= 2 and all(v in (0.0, 1.0) for v in ent)
    return indicator, all(v >= 0 for v in ent)


def sample_domain(spec, rng):
    """Mirror of consensus.sample_params with rules (a) and (b)."""
    from admitor import consensus
    out = {}
    for name, s in spec.items():
        if "base" in s:
            indicator, nonneg = domain_of(s["base"])
            if indicator:
                out[name] = s["base"]
                continue
        else:
            nonneg = False
        if "perturb" in s:
            cfg = dict(s["perturb"])
            if nonneg and cfg.get("mode") != "rel":
                lo, hi = sorted((cfg["lo"], cfg["hi"]))
                cfg["lo"], cfg["hi"] = max(lo, 0), max(hi, 0)
            out[name] = consensus._sample_one(s["base"], cfg, rng)
        elif s.get("mode") == "rel":
            out[name] = consensus._sample_one(s["base"], {"mode": "rel", "r": s.get("r", 0.3)}, rng)
        elif s.get("mode") == "range":
            n = s.get("size", 1)
            lo, hi = sorted((s["lo"], s["hi"]))
            vals = [rng.uniform(lo, hi) for _ in range(n)]
            if s.get("integer"):
                vals = [round(v) for v in vals]
            out[name] = vals if n > 1 else vals[0]
        else:
            raise ValueError("unknown spec for %s" % name)
    return out


def out_of_domain(spec, draw):
    """Names of parameters whose drawn value leaves the base value's domain."""
    bad = []
    for name, s in spec.items():
        if "base" not in s or name not in draw:
            continue
        indicator, nonneg = domain_of(s["base"])
        ent = numeric_entries(draw[name])
        if ent is None:
            continue
        if (indicator and any(v not in (0.0, 1.0) for v in ent)) or (nonneg and any(v < 0 for v in ent)):
            bad.append(name)
    return bad


# ---- one problem ----
def solve_all(cands, params):
    row = {}
    for c in cands:
        try:
            r = c.solve(params)
            ok = r.status == "optimal" and r.objective is not None
            row[c.id] = (float(r.objective) if ok else None, r.status)
        except Exception as e:
            row[c.id] = (None, "exception:" + type(e).__name__)
    return row


def run_problem(args):
    runs, sid, timeout = args
    t0 = time.time()
    d = os.path.join(runs, sid)
    try:
        from admitor import consensus
        from admitor.generate import make_candidate
        spec = json.load(open(os.path.join(d, "spec.json"), encoding="utf-8"))["spec"]
        cands = []
        for c in ORDER:
            f = os.path.join(d, c + ".py")
            if os.path.isfile(f):
                cands.append(make_candidate(open(f, encoding="utf-8").read(), c, FAMILY[c], STRATEGY[c], timeout=timeout))
        if not cands:
            return dict(sample_id=sid, status="no_stored_programs")
        bp = consensus.base_params(spec)
        if bp is None:
            return dict(sample_id=sid, status="no_base_params")
        base_row = solve_all(cands, bp)
        alive = [c for c in cands if base_row[c.id][0] is not None]
        spec_doms = {n: domain_of(s["base"]) for n, s in spec.items() if "base" in s}
        res = dict(sample_id=sid, status="ok", candidates=[c.id for c in cands],
                   n_params=len(spec), n_indicator=sum(1 for v in spec_doms.values() if v[0]),
                   n_nonneg=sum(1 for v in spec_doms.values() if v[1]), variants={})
        for var in VARIANTS:
            rng = random.Random(SEED)
            sampler = consensus.sample_params if var in ("orig", "screen1") else sample_domain
            need = {"orig": 0, "domain": 0, "screen1": 1, "domain_screen1": 1, "domain_screen2": 2}[var]
            rows, attempts, ood = [base_row], [], 0
            for _k in range(M):
                row = None
                for att in range(1, MAX_ATTEMPTS + 1):
                    draw = sampler(spec, rng)
                    row = solve_all(cands, draw)
                    last_draw = draw
                    if need == 0:
                        break
                    pool = alive if need == 1 else cands
                    if sum(1 for c in pool if row[c.id][0] is not None) >= need:
                        break
                attempts.append(att)
                ood += bool(out_of_domain(spec, last_draw))
                rows.append(row)
            res["variants"][var] = dict(
                objectives={c.id: [r[c.id][0] for r in rows] for c in cands},
                statuses={c.id: [r[c.id][1] for r in rows] for c in cands},
                attempts=attempts, draws_out_of_domain=ood)
        res["seconds"] = round(time.time() - t0, 1)
        return res
    except Exception as e:
        return dict(sample_id=sid, status="error:%s:%s" % (type(e).__name__, str(e)[:200]))


def list_ids(runs):
    return sorted(s for s in os.listdir(runs) if os.path.isfile(os.path.join(runs, s, "verdict_full.json")))


def read_results(path):
    res = {}
    if os.path.isfile(path):
        for line in open(path, encoding="utf-8"):
            if line.strip():
                r = json.loads(line)
                res[r["sample_id"]] = r  # last line wins
    return res


def cmd_run(a):
    os.makedirs(a.out, exist_ok=True)
    path = os.path.join(a.out, "results.jsonl")
    done = read_results(path)
    ids = list_ids(a.runs)
    if a.ids:
        todo = [l.strip() for l in open(a.ids, encoding="utf-8") if l.strip()]
    else:
        todo = [s for s in ids if s not in done or done[s].get("status") != "ok"]
    if a.limit:
        todo = todo[: a.limit]
    print("problems: %d, already done: %d, to run: %d" % (len(ids), len(done), len(todo)), flush=True)
    jobs = [(a.runs, s, a.timeout) for s in todo]
    t0 = time.time()
    with open(path, "a", encoding="utf-8") as fh:
        def sink(n, r):
            fh.write(json.dumps(r) + "\n"); fh.flush()
            print("  [%d/%d] %s %s %ss (%.0fs elapsed)" % (n, len(jobs), r["sample_id"], r["status"],
                                                            r.get("seconds", "-"), time.time() - t0), flush=True)
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
    labels = load_labels(a.set, a.labels)
    grade = make_grader(a.set)
    res = read_results(os.path.join(a.out, "results.jsonl"))
    ids = list_ids(a.runs)
    missing = [s for s in ids if s not in res or res[s].get("status") != "ok"]
    if missing:
        print("STOP G3: %d problems without an ok result, e.g. %s" % (len(missing), missing[:8])); sys.exit(2)

    # G1: variant orig reproduces the stored run
    bad_dec, bad_val = [], []
    for sid in ids:
        v = json.load(open(os.path.join(a.runs, sid, "verdict_full.json"), encoding="utf-8"))
        o = res[sid]["variants"]["orig"]["objectives"]
        cids = [c for c in ORDER if c in o]
        d, q, inf, _ = decide(o, cids)
        if (d, q, inf) != (v["decision"], v["clique"], v["informative"]):
            bad_dec.append(sid)
        for c in cids:
            st = (list(v["objectives"].get(c) or []) + [None] * (M + 1))[: M + 1]
            for k in range(M + 1):
                x, y = o[c][k], st[k]
                if (x is None) != (y is None) or (x is not None and not close(x, y)):
                    bad_val.append("%s:%s:%d" % (sid, c, k))
    if bad_dec or bad_val:
        print("STOP G1: orig differs from the stored runs. decisions: %d %s; values: %d %s"
              % (len(bad_dec), bad_dec[:10], len(bad_val), bad_val[:10]))
        open(os.path.join(a.out, "g1_mismatch_ids.txt"), "w", encoding="utf-8").write(
            "\n".join(sorted(set(bad_dec) | {x.split(":")[0] for x in bad_val})) + "\n")
        sys.exit(2)

    scope = [s for s in ids if s in labels and not (a.set == "stream" and s in DEV)]
    judges = ["panel_base_2of3", "panel_base_3of3", "gate_mi3", "gate_mi1", "gate3_mi3", "gate3_mi1",
              "base2_kept", "base2_lost_uninformative", "base2_lost_failure", "base2_lost_divergence",
              "base3_kept", "base3_lost_uninformative", "base3_lost_failure", "base3_lost_divergence", "base3_lost_shrink"]
    rows, per_problem, facts = [], [], dict(set=a.set, problems=len(ids), graded=len(scope), variants={})
    cert_all = {}
    for var in VARIANTS:
        cert = {j: {} for j in judges}
        att, ood, ninf = [], 0, Counter()
        for sid in ids:
            vv = res[sid]["variants"][var]
            o = vv["objectives"]
            cids = [c for c in ORDER if c in o]
            bv = {c: o[c][0] for c in cids if o[c][0] is not None}
            c2, c3, grp = panel_judgements(bv)
            d, q, inf, val = decide(o, cids)
            _, q1, _, val1 = decide(o, cids, min_inf=1)
            cert["panel_base_2of3"][sid], cert["panel_base_3of3"][sid] = c2, c3
            cert["gate_mi3"][sid], cert["gate_mi1"][sid] = val, val1
            cert["gate3_mi3"][sid] = val if len(q) == 3 else None
            cert["gate3_mi1"][sid] = val1 if len(q1) == 3 else None
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
                    div = any(o[x][k] is not None and o[y][k] is not None and not close(o[x][k], o[y][k])
                              for x, y in itertools.combinations(g, 2) for k in rs)
                    t = "lost_divergence" if div else "lost_failure"
                elif len(q) < need:
                    t = "lost_shrink"
                else:
                    t = "kept"
                if pref + "_" + t in cert:
                    cert[pref + "_" + t][sid] = base_val
            att += vv["attempts"]
            ood += vv["draws_out_of_domain"]
            ninf[len(inf)] += 1
            per_problem.append(dict(sample_id=sid, variant=var, decision=d, clique=";".join(q), informative=len(inf),
                                    certificate=val, base2=c2, base3=c3, label=labels.get(sid),
                                    wrong=(None if val is None or sid not in labels else not grade(val, labels[sid])),
                                    attempts=sum(vv["attempts"]), draws_out_of_domain=vv["draws_out_of_domain"]))
        cert_all[var] = cert
        for j in judges:
            n = k = 0
            for sid in scope:
                val = cert[j].get(sid)
                if val is None:
                    continue
                n += 1
                k += not grade(val, labels[sid])
            rows.append(dict(variant=var, judge=j, certified=n, wrong=k, correct=n - k,
                             false_pct=round(100.0 * k / n, 1) if n else "",
                             coverage_pct=round(100.0 * n / len(scope), 1)))
        facts["variants"][var] = dict(
            draws=len(att), mean_attempts=round(sum(att) / len(att), 3),
            draws_at_max_attempts=sum(1 for x in att if x == MAX_ATTEMPTS),
            draws_out_of_domain=ood, informative_instances=dict(sorted(ninf.items())))

    # G2: stated-instance judges do not depend on the variant
    for j in ("panel_base_2of3", "panel_base_3of3"):
        ref = cert_all["orig"][j]
        for var in VARIANTS[1:]:
            if cert_all[var][j] != ref:
                print("STOP G2: %s differs between orig and %s" % (j, var)); sys.exit(2)
    print("GATES PASSED (G1, G2, G3)")

    facts["indicator_parameters"] = sum(res[s]["n_indicator"] for s in ids)
    facts["problems_with_indicator_parameter"] = sum(1 for s in ids if res[s]["n_indicator"])
    facts["problems_with_out_of_domain_draw_orig"] = sum(1 for s in ids if res[s]["variants"]["orig"]["draws_out_of_domain"])
    facts["solve_seconds_total"] = round(sum(res[s].get("seconds", 0) for s in ids), 1)

    with open(os.path.join(a.out, "redraw_problem_level.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    md = ["| Variant | Judge | Certified | Wrong | Correct | False % | Coverage % |", "|---|---|---:|---:|---:|---:|---:|"]
    md += ["| `%s` | `%s` | %d | %d | %d | %s | %s |" % (r["variant"], r["judge"], r["certified"], r["wrong"],
                                                         r["correct"], r["false_pct"], r["coverage_pct"]) for r in rows]
    open(os.path.join(a.out, "redraw_problem_level.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    with open(os.path.join(a.out, "redraw_per_problem.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(per_problem[0])); w.writeheader(); w.writerows(per_problem)
    json.dump(facts, open(os.path.join(a.out, "redraw_facts.json"), "w", encoding="utf-8"), indent=2)

    if a.set == "stream":
        for var in VARIANTS:
            for j in ("gate_mi3", "gate_mi1", "gate3_mi3", "gate3_mi1"):
                dj = os.path.join(a.out, "verdicts", "%s__%s" % (var, j))
                os.makedirs(dj, exist_ok=True)
                for sid in ids:
                    val = cert_all[var][j].get(sid)
                    doc = {"sample_id": sid, "decision": "ACCEPT" if val is not None else "ABSTAIN",
                           "clique_value": float(val) if val is not None else None}
                    with open(os.path.join(dj, sid + ".json"), "w", encoding="utf-8", newline="\n") as fh:
                        json.dump(doc, fh, ensure_ascii=False)
    print("\n".join(md))
    print(json.dumps(facts, indent=2))


def main():
    ap = argparse.ArgumentParser(description="Domain-restricted and screened resampling (solver only).")
    ap.add_argument("mode", choices=["run", "summarize"])
    ap.add_argument("--set", required=True, choices=["stream", "calib"])
    ap.add_argument("--runs", required=True)
    ap.add_argument("--labels", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--timeout", type=int, default=60)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--ids", default="")
    a = ap.parse_args()
    (cmd_run if a.mode == "run" else cmd_summarize)(a)


if __name__ == "__main__":
    main()
