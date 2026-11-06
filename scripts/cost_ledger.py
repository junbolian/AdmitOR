# -*- coding: utf-8 -*-
"""Cost ledger of one certification on the E1 stream (zero token).

Purpose
    Counts the model calls, the text volume per call and the solver time of
    one certification over the 298 stream certifications of E1. No model is
    called. The only programs executed are the stored candidate programs, on
    the stored instances, for the timing sample in part (c).

Parts
    (a) model calls per problem: 1 extraction call (admitor/ir_extract.py),
        3 candidate generations (admitor/pipeline_one.py live_run) and the
        repair rounds of admitor/generate.py gen_candidate (retries=1: one
        regeneration after a failed probe on the stated instance). The repair
        rounds were printed to stdout only; the certification client was not
        wrapped by runlog, and the run records keep neither raw responses nor
        that stdout. They are reported as not recorded and are not inferred.
    (b) text volume per call, from stored text only:
          extraction request  EXTRACT_PROMPT with the work-order question
          extraction response the `raw` field of spec.json, re-serialized as
                              compact JSON (the original response text is not
                              stored, so its whitespace is unknown: estimated)
          generation request  CANDIDATE_PROMPT filled exactly as live_run fills
                              it (stack, strategy rule, parameter meanings from
                              spec.json raw, question): measured
          generation response the stored program <candidate>.py, which is the
                              last code block of the final response; text
                              outside that block is not stored, so this is a
                              lower bound of the response
        Token counts need tiktoken (o200k_base); it is reported as not
        measured when tiktoken is not installed.
    (c) wall-clock time: elapsed_s of every compact certification verdict
        (artifacts/e1/certify_verdicts, written by scripts/e1_certify.py),
        which covers the whole certification (model calls and solver runs).
        The solver share is re-measured on a sample of 30 problems drawn with
        random.Random(20261106).sample(sorted(sample_ids), 30): every stored
        program is re-run on its six stored instances (instantiations in
        verdict_full.json) through admitor.generate.make_candidate with the
        60 s timeout of scripts/feasibility_resampling.py. Each re-run is
        compared with the stored objective under the agreement rule
        abs(a - b) <= 1e-4 * max(1, |a|, |b|), with run_l3's rule that a
        value counts only when the status is optimal; differences are
        counted and reported, nothing is changed.
    (d) one table, every cell marked measured, estimated or not recorded.

Inputs
    --runs-full          <run records>/outputs/e1/certify_runs (verdict_full.json,
                         spec.json, <candidate>.py; release asset, not in git)
    --work-order         <run records>/outputs/e1/gate_workorder.jsonl (release asset)
    --certify-verdicts   artifacts/e1/certify_verdicts (in git)
    --out                default outputs/additional_2026-11
    --sample-n, --seed, --timeout   timing sample, defaults 30, 20261106, 60
    --skip-solve         skip the re-runs of part (c)

Outputs
    <out>/cost_ledger.md        the ledger
    <out>/cost_ledger_solves.csv one row per timed re-run

Measured versus estimated
    Measured: call counts that follow from stored files, request characters,
    program characters, elapsed_s per certification, re-run solver seconds on
    this machine. Estimated: extraction response characters (re-serialized),
    counts that follow from the code path only (3 generations and 3 probe
    solves per problem). Not recorded: repair rounds, per-call latency.

Reproduce (from the repository root)
    python scripts/cost_ledger.py --runs-full <run records>/outputs/e1/certify_runs \\
        --work-order <run records>/outputs/e1/gate_workorder.jsonl
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import random
import shutil
import statistics
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))  # repository root, for admitor/
from admitor.generate import CANDIDATE_PROMPT, STRUCTURED_EXTRA, make_candidate  # noqa: E402
from admitor.ir_extract import EXTRACT_PROMPT  # noqa: E402

ORDER = ["A-direct", "B-structured", "C-direct"]
FAMILY = {"A-direct": "deepseek", "B-structured": "gpt", "C-direct": "claude"}
STRATEGY = {"A-direct": "direct", "B-structured": "structured", "C-direct": "direct"}
PYOMO_STACK = (
    "pyomo with the HiGHS solver. Solve EXACTLY like this: from pyomo.contrib.appsi.solvers.highs "
    "import Highs; Highs().solve(model); then obj_val = float(pyo.value(<your objective component>)) "
    "and return {'objective': obj_val, 'status': 'optimal'}. Determine success ONLY by whether the "
    "objective value is retrievable (pyo.value raises otherwise); NEVER compare termination-condition enums"
)
STACK = {"A-direct": PYOMO_STACK, "B-structured": PYOMO_STACK, "C-direct": "gurobipy"}
TOL = 1e-4


def close(a, b):
    return abs(a - b) <= TOL * max(1.0, abs(a), abs(b))


def med(xs):
    return statistics.median(xs) if xs else None


def fmt(x, nd=0):
    if x is None:
        return "-"
    return ("{:,.%df}" % nd).format(x)


def token_counter():
    try:
        import tiktoken  # noqa: F401
    except ImportError:
        return None
    enc = tiktoken.get_encoding("o200k_base")
    return lambda s: len(enc.encode(s))


def main():
    ap = argparse.ArgumentParser(description="Cost ledger of one certification (zero token).")
    ap.add_argument("--runs-full", required=True)
    ap.add_argument("--work-order", required=True)
    ap.add_argument("--certify-verdicts", default="artifacts/e1/certify_verdicts")
    ap.add_argument("--out", default="outputs/additional_2026-11")
    ap.add_argument("--sample-n", type=int, default=30)
    ap.add_argument("--seed", type=int, default=20261106)
    ap.add_argument("--timeout", type=int, default=60)
    ap.add_argument("--skip-solve", action="store_true")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    tok = token_counter()

    questions = {}
    for line in open(a.work_order, encoding="utf-8"):
        if line.strip():
            r = json.loads(line)
            questions[str(r["sample_id"])] = str(r.get("question", ""))
    sample_ids = sorted(d for d in os.listdir(a.runs_full)
                        if os.path.isfile(os.path.join(a.runs_full, d, "verdict_full.json")))
    if len(sample_ids) != 298:
        print("STOP: expected 298 certify runs, found %d" % len(sample_ids)); sys.exit(2)

    # (a) and (b): calls and text volume
    text = {k: [] for k in ["extract_req", "extract_resp"] + ["gen_req_" + c for c in ORDER]
            + ["gen_resp_" + c for c in ORDER]}
    n_spec = 0
    n_prog = {c: 0 for c in ORDER}
    n_status = {"stated": 0, "resampled": 0}
    n_inst = []
    for sid in sample_ids:
        d = os.path.join(a.runs_full, sid)
        q = questions[sid]
        spec = json.load(open(os.path.join(d, "spec.json"), encoding="utf-8"))
        v = json.load(open(os.path.join(d, "verdict_full.json"), encoding="utf-8"))
        n_spec += 1
        text["extract_req"].append(EXTRACT_PROMPT.replace("{question}", q))
        text["extract_resp"].append(json.dumps(spec.get("raw"), ensure_ascii=False))
        pd = "\n".join("  %s: %s" % (k, p.get("meaning", "")) for k, p in spec["raw"]["params"].items())
        for c in ORDER:
            text["gen_req_" + c].append(CANDIDATE_PROMPT.format(
                stack=STACK[c], strategy_extra=STRUCTURED_EXTRA if STRATEGY[c] == "structured" else "",
                param_desc=pd, question=q))
            p = os.path.join(d, c + ".py")
            if os.path.isfile(p):
                n_prog[c] += 1
                text["gen_resp_" + c].append(open(p, encoding="utf-8").read())
        k = len(v["instantiations"])
        n_inst.append(k)
        for c in ORDER:
            st = v["statuses"].get(c) or []
            n_status["stated"] += 1 if (k == 6 and st) else 0
            n_status["resampled"] += len(st) - (1 if k == 6 and st else 0)
    chars = {k: [len(s) for s in xs] for k, xs in text.items()}
    toks = {k: [tok(s) for s in xs] for k, xs in text.items()} if tok else None

    # (c) elapsed_s of every certification
    elapsed = []
    for sid in sample_ids:
        p = os.path.join(a.certify_verdicts, sid + ".json")
        if os.path.isfile(p):
            e = json.load(open(p, encoding="utf-8")).get("elapsed_s")
            if e is not None:
                elapsed.append(float(e))

    # (c) solver re-runs on the timing sample
    timed = random.Random(a.seed).sample(sorted(sample_ids), a.sample_n)
    rows = []
    if not a.skip_solve:
        tmp_root = tempfile.mkdtemp(prefix="cost_ledger_")
        old_tmp = tempfile.tempdir
        tempfile.tempdir = tmp_root
        try:
            for n, sid in enumerate(timed, 1):
                d = os.path.join(a.runs_full, sid)
                v = json.load(open(os.path.join(d, "verdict_full.json"), encoding="utf-8"))
                insts = v["instantiations"]
                for c in ORDER:
                    p = os.path.join(d, c + ".py")
                    if not os.path.isfile(p):
                        continue
                    cand = make_candidate(open(p, encoding="utf-8").read(), c, FAMILY[c], STRATEGY[c],
                                          timeout=a.timeout)
                    for k, params in enumerate(insts):
                        t0 = time.perf_counter()
                        r = cand.solve(params)
                        dt = time.perf_counter() - t0
                        new = float(r.objective) if (r.status == "optimal" and r.objective is not None) else None
                        old = v["objectives"][c][k]
                        same = (new is None and old is None) or (
                            new is not None and old is not None and close(new, old))
                        rows.append(dict(sample_id=sid, candidate=c, instance=k,
                                         kind="stated" if (k == 0 and len(insts) == 6) else "resampled",
                                         seconds=round(dt, 3), status=r.status[:60], objective=new,
                                         stored_objective=old, reproduces=same))
                print("[%d/%d] %s timed" % (n, len(timed), sid), flush=True)
        finally:
            tempfile.tempdir = old_tmp
            shutil.rmtree(tmp_root, ignore_errors=True)
        with open(os.path.join(a.out, "cost_ledger_solves.csv"), "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

    def per_problem(kind=None):
        acc = {}
        for r in rows:
            if kind is None or r["kind"] == kind:
                acc[r["sample_id"]] = acc.get(r["sample_id"], 0.0) + r["seconds"]
        return list(acc.values())

    sec_solve = {kd: [r["seconds"] for r in rows if r["kind"] == kd] for kd in ("stated", "resampled")}
    n_diff = sum(1 for r in rows if not r["reproduces"])
    N = len(sample_ids)

    def tcell(key):
        if toks is None:
            return "not measured (tiktoken not installed)"
        return "%s (approximate, measured)" % fmt(med(toks[key]))

    L = ["# Cost ledger of one certification (E1 stream, %d certifications)" % N, "",
         "No model is called to produce this ledger. Cells are marked **measured** (from stored files or "
         "re-runs), **estimated** (from the code path, or from a re-serialization of stored text) or "
         "**not recorded**.", "",
         "| Row | Count per problem | Total over the %d problems | Median characters (request / response) "
         "| Median approx. tokens (request / response) | Median seconds |" % N,
         "|---|---|---|---|---|---|"]
    L.append("| Extraction (model A, max_tokens 8192) | 1 (measured: spec.json) | %d (measured) | %s / %s "
             "(request measured; response estimated, re-serialized `raw`) | %s | not recorded per call |" % (
                 n_spec, fmt(med(chars["extract_req"])), fmt(med(chars["extract_resp"])),
                 tcell("extract_req") if toks is None else "%s / %s" % (tcell("extract_req"), tcell("extract_resp"))))
    for c in ORDER:
        L.append("| Generation %s (%s) | 1 (estimated: code path, one call per candidate) | %d "
                 "(estimated: code path); %d stored programs (measured) | %s / %s (request measured; "
                 "response measured as the stored program, a lower bound) | %s | not recorded per call |" % (
                     c, FAMILY[c], N, n_prog[c], fmt(med(chars["gen_req_" + c])),
                     fmt(med(chars["gen_resp_" + c])),
                     tcell("gen_req_" + c) if toks is None else "%s / %s" % (
                         tcell("gen_req_" + c), tcell("gen_resp_" + c))))
    L.append("| Repair rounds (regeneration after a failed probe) | not recorded (code path allows 0 to 3) "
             "| not recorded | not recorded | not recorded | not recorded |")
    L.append("| Probe solves at the stated instance (generation side) | 3 (estimated: code path, one per "
             "candidate before certification) | %d (estimated) | - | - | not recorded |" % (3 * N))
    L.append("| Solver runs at the stated instance (certification) | 3 (measured: stored statuses) | %d "
             "(measured) | - | - | %s per solve; %s per problem (measured, re-run on %d problems) |" % (
                 n_status["stated"], fmt(med(sec_solve["stated"]), 2), fmt(med(per_problem("stated")), 2),
                 len(timed) if rows else 0))
    L.append("| Solver runs at the five resampled instances | 15 (measured: stored statuses) | %d (measured) "
             "| - | - | %s per solve; %s per problem (measured, re-run on %d problems) |" % (
                 n_status["resampled"], fmt(med(sec_solve["resampled"]), 2),
                 fmt(med(per_problem("resampled")), 2), len(timed) if rows else 0))
    L.append("| Whole certification (elapsed_s, model calls and solver runs) | 1 | %d verdicts (measured) "
             "| - | - | %s median; %s total (measured, stored elapsed_s) |" % (
                 len(elapsed), fmt(med(elapsed), 1), fmt(sum(elapsed), 1)))
    L += ["", "The majority-vote judge makes no additional model call, because it reads the host's three "
          "stored rollouts.", "",
          "## Text volume per role (characters)", "",
          "| Role | Median | Total | Status |", "|---|---:|---:|---|"]
    labels = [("extract_req", "Extraction request", "measured"),
              ("extract_resp", "Extraction response (re-serialized `raw`)", "estimated")]
    for c in ORDER:
        labels += [("gen_req_" + c, "Generation request %s" % c, "measured"),
                   ("gen_resp_" + c, "Generation response %s (stored program)" % c, "measured, lower bound")]
    for key, lab, st in labels:
        L.append("| %s | %s | %s | %s |" % (lab, fmt(med(chars[key])), fmt(sum(chars[key])), st))
    L += ["", "## Notes", "",
          "- Stream: %d certifications with a run folder; instances per verdict: %s." % (
              N, dict(sorted({k: n_inst.count(k) for k in set(n_inst)}.items()))),
          "- Two further work-order items (sample_108, sample_244) ended with an ERROR verdict after "
          "the extraction call (extractor output not parseable JSON); they made one extraction call each "
          "and are outside the %d." % N,
          "- Programs missing from the run folders: %s (the extracted program was empty, so "
          "scripts/e1_certify.py wrote no file; its six runs are stored as KeyError 'solve' crashes)." % (
              ", ".join("%s %d" % (c, N - n_prog[c]) for c in ORDER if N - n_prog[c]) or "none"),
          "- Repair rounds: gen_candidate prints `[gen] <candidate>: base-instance probe failed` and "
          "regenerates once. The certification client in pipeline_one.live_run is not wrapped by "
          "runlog, scripts/e1_certify.py stores only the final program, and its stdout is not part of "
          "the run records, so the number of repair rounds is not recorded. Each repair round adds one "
          "model call and lengthens that call's request by the previous program and its status.",
          "- Seconds per call of extraction and generation are not recorded; elapsed_s covers the whole "
          "certification.",
          "- Solver timings are wall-clock seconds of make_candidate's subprocess (interpreter start, "
          "imports, model build and solve), re-measured on %s with timeout %d s, sequentially." % (
              time.strftime("%Y-%m-%d"), a.timeout)]
    if rows:
        L += ["- Timing sample (random.Random(%d).sample(sorted(sample_ids), %d)): %s." % (
                  a.seed, a.sample_n, ", ".join(timed)),
              "- Re-runs: %d; per solve median %s s (all), per problem median %s s (all runs of the "
              "problem), total %s s." % (len(rows), fmt(med([r["seconds"] for r in rows]), 2),
                                        fmt(med(per_problem()), 2), fmt(sum(r["seconds"] for r in rows), 1)),
              "- Reproduction under the agreement rule: %d of %d re-runs differ from the stored objective "
              "value (listed in cost_ledger_solves.csv, column reproduces)." % (n_diff, len(rows))]
    open(os.path.join(a.out, "cost_ledger.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
