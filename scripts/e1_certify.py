# -*- coding: utf-8 -*-
"""AdmitOR E1 -- e1_certify.py (v0.1)

Batch certification over a problem file (--work-order): for every problem, run the
AdmitOR pipeline (extract spec -> three families -> L3 resampled consensus)
and emit one verdict json per sample in exactly the format GateOracle reads:
    <verdicts_dir>/<sample_id>.json
    {"sample_id", "decision", "clique_value", "clique", "families",
     "informative", "notes", "run_dir"}

Resumable: samples whose verdict file already exists are skipped, so the
batch can be wrapped in the same restart loop as everything else. Any
per-sample exception writes an ERROR verdict (decision "ERROR", certified
nothing) and continues -- GateOracle treats non-ACCEPT as no-admission, so
a crashed certification can never admit a candidate.

Inputs
    --work-order    jsonl with one {"sample_id", "question"} object per line
    --verdicts-dir  output directory for the compact GateOracle verdicts
    --runs-dir      output directory for the per-sample rich run artifacts
    --m             number of resampled instantiations (default 5)
    --limit         stop after this many certifications (0 means no limit)
    --only          comma-separated sample_ids to (re)certify
    --sampler       independent (default) or param_screen
    --both          also store the verdict of the other sampler

Outputs
    <verdicts-dir>/<sample_id>.json   compact verdict, the GateOracle format
    <runs-dir>/<sample_id>/spec.json          extracted specification
    <runs-dir>/<sample_id>/<candidate>.py     generated solver scripts
    <runs-dir>/<sample_id>/verdict_full.json  full verdict with clique geometry
    A one-line JSON summary is printed at the end.

Environment (live mode, read from the environment only)
    ADMITOR_API_KEY / ADMITOR_BASE_URL / ADMITOR_MODEL_A / _B / _C, or per
    family ADMITOR_API_KEY_A / _B / _C and ADMITOR_BASE_URL_A / _B / _C (the
    shared variables are the fallback); optional ADMITOR_EXTRA_JSON_A / _B / _C,
    ADMITOR_USAGE_LOG and ADMITOR_CANDIDATES_PER_FAMILY (see
    admitor/pipeline_one.py)

Cost: this step calls the model. It is the expensive step of E1.

Example invocation (from the repository root)
    python scripts/e1_certify.py \\
        --work-order outputs/e1/gate_workorder.jsonl \\
        --verdicts-dir outputs/e1/verdicts \\
        --runs-dir outputs/e1/certify_runs
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import asdict

# Make the repository root importable so `admitor` resolves no matter which
# directory the script is invoked from.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from admitor.consensus import run_l3, run_l3_param_screen  # noqa: E402
from admitor.ir_extract import ExtractionFailed  # noqa: E402
from admitor.pipeline_one import live_run  # noqa: E402


def certify_one(question: str, m: int, run_dir: str, sampler: str = "independent",
                both: bool = False) -> dict:
    try:
        spec, cands = live_run(question)
    except ExtractionFailed as exc:  # every extraction attempt failed: record them, then ERROR
        os.makedirs(run_dir, exist_ok=True)
        json.dump(exc.attempts, open(os.path.join(run_dir, "extraction_attempts.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
        raise
    os.makedirs(run_dir, exist_ok=True)
    attempts = spec.get("extraction_attempts", [])
    json.dump(attempts, open(os.path.join(run_dir, "extraction_attempts.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    json.dump(
        {"spec": spec["spec"], "warnings": spec.get("warnings", []), "raw": spec.get("raw"),
         "extraction_attempts": attempts},
        open(os.path.join(run_dir, "spec.json"), "w", encoding="utf-8"),
        ensure_ascii=False,
        indent=2,
    )
    for c in cands:
        if getattr(c, "code", None):
            open(os.path.join(run_dir, f"{c.id}.py"), "w", encoding="utf-8").write(c.code)
    def _dump(obj, name):
        json.dump(obj, open(os.path.join(run_dir, name), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)

    # verdict_full.json holds the verdict of the chosen sampler. With --both
    # the other sampler is run on the same candidates and stored next to it
    # (verdict_independent.json or verdict_param_screen.json).
    v_ind = v_ps = info = None
    if sampler == "independent" or both:
        v_ind = run_l3(cands, spec["spec"], m=m, seed=42)
    if sampler == "param_screen" or both:
        v_ps, info = run_l3_param_screen(cands, spec["spec"], m=m, seed=42)
        _dump(info, "param_screen.json")
    v = v_ps if sampler == "param_screen" else v_ind
    _dump(asdict(v), "verdict_full.json")
    if both:
        if sampler == "param_screen":
            _dump(asdict(v_ind), "verdict_independent.json")
        else:
            _dump(asdict(v_ps), "verdict_param_screen.json")
    clique_value = None
    if v.decision == "ACCEPT" and v.clique:
        try:
            clique_value = v.objectives[v.clique[0]][0]  # base instance
        except (KeyError, IndexError):
            clique_value = None
    return {
        "decision": v.decision,
        "clique_value": clique_value,
        "clique": list(v.clique),
        "families": list(v.families),
        "informative": list(v.informative),
        "notes": list(v.notes),
        "warnings": spec.get("warnings", []),
        "extraction_attempts": len(attempts),
        "extraction_failures": [a["error"] for a in attempts if a.get("status") == "failed"],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-order", required=True)
    ap.add_argument("--verdicts-dir", required=True)
    ap.add_argument("--runs-dir", required=True)
    ap.add_argument("--m", type=int, default=5)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--only", default="", help="comma-separated sample_ids to (re)certify")
    ap.add_argument("--sampler", choices=["independent", "param_screen"], default="independent",
                    help="resampling of the instances: independent draws of every parameter, "
                         "or joint draws over the parameters that keep the candidates solvable")
    ap.add_argument("--both", action="store_true",
                    help="also run the other sampler on the same candidates and store its verdict")
    a = ap.parse_args()

    # Preflight: a missing key would fail every sample instantly and litter
    # the verdicts dir with 300 ERROR files. Refuse up front instead.
    if not os.environ.get("ADMITOR_API_KEY") and not all(
        os.environ.get("ADMITOR_API_KEY_" + f) for f in ("A", "B", "C")
    ):
        raise SystemExit(
            "ADMITOR_API_KEY is not set in this shell -- set ADMITOR_API_KEY "
            "/ ADMITOR_BASE_URL / ADMITOR_MODEL_A/B/C (see the Quickstart "
            "section of the README) and rerun. No verdicts were written."
        )

    only = {s.strip() for s in a.only.split(",") if s.strip()}
    items = []
    with open(a.work_order, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    os.makedirs(a.verdicts_dir, exist_ok=True)

    done = skipped = errors = accepted = 0
    for item in items:
        sid = str(item.get("sample_id", "")).strip()
        if not sid:
            continue
        if only and sid not in only:
            continue
        out_path = os.path.join(a.verdicts_dir, f"{sid}.json")
        if os.path.isfile(out_path) and not only:
            skipped += 1
            continue
        t0 = time.time()
        run_dir = os.path.join(a.runs_dir, sid)
        try:
            verdict = certify_one(str(item.get("question", "")), a.m, run_dir,
                                  sampler=a.sampler, both=a.both)
        except Exception as exc:  # sample-fatal only, never batch-fatal
            verdict = {
                "decision": "ERROR",
                "clique_value": None,
                "clique": [],
                "families": [],
                "informative": [],
                "notes": [f"certification error: " f"{type(exc).__name__}: {exc}"[:300]],
                "warnings": [],
            }
            if isinstance(exc, ExtractionFailed):
                verdict["extraction_attempts"] = len(exc.attempts)
                verdict["extraction_failures"] = [x["error"] for x in exc.attempts]
            errors += 1
        verdict.update(
            {
                "sample_id": sid,
                "run_dir": run_dir,
                "elapsed_s": round(time.time() - t0, 1),
                "m": a.m,
                "seed": 42,
                "sampler": a.sampler,
            }
        )
        tmp = out_path + ".tmp"
        json.dump(verdict, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        os.replace(tmp, out_path)
        done += 1
        accepted += int(verdict["decision"] == "ACCEPT")
        print(
            f"[{done}] {sid}: {verdict['decision']}"
            + (f" value={verdict['clique_value']}" if verdict["decision"] == "ACCEPT" else ""),
            flush=True,
        )
        if a.limit and done >= a.limit:
            break

    print(
        json.dumps(
            {
                "certified_this_run": done,
                "skipped_existing": skipped,
                "errors": errors,
                "accepted": accepted,
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
