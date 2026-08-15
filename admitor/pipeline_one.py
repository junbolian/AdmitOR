# -*- coding: utf-8 -*-
"""AdmitOR core -- pipeline_one.py (v0.4)

Single-problem end-to-end pipeline: extract spec -> three candidates -> L3.

Purpose
    Certify one natural-language optimization problem end to end. The
    extractor produces a base-anchored parameter-domain specification, three
    model families each write an independent solver script against that
    shared specification, and L3 resampled consensus decides ACCEPT, ABSTAIN
    or UNINFORMATIVE.

Inputs
    --mock                offline self-test, no network and no credentials
    --question <file>     UTF-8 text file holding one problem statement
    --m <int>             number of resampled instantiations (default 5)

Outputs
    runs/<timestamp>/spec.json          extracted specification and warnings
    runs/<timestamp>/<candidate>.py     each family's generated solver script
    runs/<timestamp>/<candidate>.raw.txt  each family's raw model response
    runs/<timestamp>/verdict.json       the full L3 verdict
    A human-readable summary is printed to stdout.

Environment (live mode only, never read from a file)
    ADMITOR_API_KEY   required, credential for the OpenAI-compatible endpoint
    ADMITOR_BASE_URL  required, chat-completions base URL of that endpoint
    ADMITOR_MODEL_A   family A model id (default deepseek-v3.2)
    ADMITOR_MODEL_B   family B model id (default gpt-5.4)
    ADMITOR_MODEL_C   family C model id (default claude-sonnet-4-6)

Example (run from the repository root)
    python -m admitor.pipeline_one --mock
"""
import argparse
import json
import os
import sys
import time
from dataclasses import asdict

from admitor.consensus import base_params, run_l3
from admitor.generate import gen_candidate, make_candidate
from admitor.ir_extract import extract_spec

PROMO_Q = (
    "A warehouse has 150 boxes of a promo product for 3 stores; "
    "each store's shelf cap is 60. Net profit per box: store1 8, "
    "store2 6, store3 4 (CNY). Contract: each store must receive at "
    "least 20 boxes this cycle. Not all boxes must ship. Maximize "
    "net profit."
)

MOCK_SPEC = (
    '{"params": {"profit": {"meaning": "net profit per box per store", '
    '"base": [8, 6, 4], "perturb": {"mode": "abs", "lo": 9.0, '
    '"hi": -2.0, "integer": false}}}, "objective_sense": "max"}'
)

_CODE_OK = """
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs
def solve(params):
    p = params["profit"]; S = range(3)
    m = pyo.ConcreteModel()
    m.x = pyo.Var(S, domain=pyo.NonNegativeReals, bounds=(0, 60))
    m.obj = pyo.Objective(expr=sum(p[i]*m.x[i] for i in S), sense=pyo.maximize)
    m.cap = pyo.Constraint(expr=sum(m.x[i] for i in S) <= 150)
    m.floor = pyo.Constraint(S, rule=lambda m,i: m.x[i] >= 20)
    Highs().solve(m)
    return {"objective": float(m.obj()), "status": "optimal"}
"""

_CODE_NOFLOOR = _CODE_OK.replace(
    "    m.floor = pyo.Constraint(S, rule=lambda m,i: m.x[i] >= 20)\n", ""
)


def mock_run():
    spec = extract_spec(PROMO_Q, lambda _: MOCK_SPEC)
    cands = [
        make_candidate(_CODE_NOFLOOR, "A-direct", "deepseek", "direct"),
        make_candidate(_CODE_OK, "B-structured", "gpt", "structured"),
        make_candidate(_CODE_OK, "C-direct", "claude", "direct"),
    ]
    return spec, cands


def live_run(question: str):
    from openai import OpenAI

    # Both are required and are read from the environment only. The gate never
    # reads credentials or endpoints from a file, and no endpoint is baked in:
    # the three candidate families are reached through whichever
    # OpenAI-compatible endpoint the operator points ADMITOR_BASE_URL at.
    api_key = os.environ.get("ADMITOR_API_KEY")
    base_url = os.environ.get("ADMITOR_BASE_URL")
    if not api_key or not base_url:
        raise SystemExit(
            "live mode needs ADMITOR_API_KEY and ADMITOR_BASE_URL in the "
            "environment (ADMITOR_BASE_URL is the OpenAI-compatible "
            "chat-completions base URL, for example https://api.openai.com/v1). "
            "Use --mock for the offline self-test, which needs neither."
        )
    client = OpenAI(api_key=api_key, base_url=base_url)
    models = {
        "A": os.environ.get("ADMITOR_MODEL_A", "deepseek-v3.2"),
        "B": os.environ.get("ADMITOR_MODEL_B", "gpt-5.4"),
        "C": os.environ.get("ADMITOR_MODEL_C", "claude-sonnet-4-6"),
    }

    def call(model, max_tokens=3000):
        def f(prompt):
            r = client.chat.completions.create(
                model=model,
                temperature=0,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            return r.choices[0].message.content or ""

        return f

    # Extraction must emit every base value (matrices included); 3000 tokens
    # truncates large-instance specs mid-JSON. Candidates stay at 3000 --
    # their code reads values from params and stays small.
    spec = extract_spec(question, call(models["A"], max_tokens=8192))
    probe = base_params(spec["spec"])
    pd = "\n".join(f"  {k}: {v.get('meaning', '')}" for k, v in spec["raw"]["params"].items())
    plan = [
        (
            "A-direct",
            "deepseek",
            "direct",
            models["A"],
            "pyomo with the HiGHS solver. Solve EXACTLY like this: from pyomo.contrib.appsi.solvers.highs import Highs; Highs().solve(model); then obj_val = float(pyo.value(<your objective component>)) and return {'objective': obj_val, 'status': 'optimal'}. Determine success ONLY by whether the objective value is retrievable (pyo.value raises otherwise); NEVER compare termination-condition enums",
        ),
        (
            "B-structured",
            "gpt",
            "structured",
            models["B"],
            "pyomo with the HiGHS solver. Solve EXACTLY like this: from pyomo.contrib.appsi.solvers.highs import Highs; Highs().solve(model); then obj_val = float(pyo.value(<your objective component>)) and return {'objective': obj_val, 'status': 'optimal'}. Determine success ONLY by whether the objective value is retrievable (pyo.value raises otherwise); NEVER compare termination-condition enums",
        ),
        ("C-direct", "claude", "direct", models["C"], "gurobipy"),
    ]
    cands = [
        gen_candidate(
            question, pd, fam, strat, stack, call(mdl), cid, probe_params=probe, retries=1
        )
        for cid, fam, strat, mdl, stack in plan
    ]
    return spec, cands


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--question")
    ap.add_argument("--m", type=int, default=5)
    a = ap.parse_args()

    if a.mock:
        spec, cands = mock_run()
    else:
        if not a.question:
            sys.exit("need --question <file> or --mock")
        q = open(a.question, encoding="utf-8").read()
        spec, cands = live_run(q)

    run_dir = os.path.join("runs", time.strftime("%Y%m%d-%H%M%S"))
    os.makedirs(run_dir, exist_ok=True)
    print("artifacts:", run_dir)
    print("spec:", spec["spec"])
    for w in spec.get("warnings", []):
        print("spec-warning:", w)
    json.dump(
        {"spec": spec["spec"], "warnings": spec.get("warnings", []), "raw": spec.get("raw")},
        open(os.path.join(run_dir, "spec.json"), "w", encoding="utf-8"),
        ensure_ascii=False,
        indent=2,
    )
    for c in cands:
        if getattr(c, "code", None):
            open(os.path.join(run_dir, f"{c.id}.py"), "w", encoding="utf-8").write(c.code)
        if getattr(c, "raw_response", None):
            open(os.path.join(run_dir, f"{c.id}.raw.txt"), "w", encoding="utf-8").write(
                c.raw_response
            )

    v = run_l3(cands, spec["spec"], m=a.m, seed=42)
    json.dump(
        asdict(v),
        open(os.path.join(run_dir, "verdict.json"), "w", encoding="utf-8"),
        ensure_ascii=False,
        indent=2,
    )
    print("decision:", v.decision)
    for note in v.notes:
        print("note:", note)
    if v.decision == "ACCEPT":
        print("clique:", v.clique, "families:", v.families)
        has_base = len(v.instantiations) == a.m + 1
        if has_base:
            print("answer at base instance (clique value):", v.objectives[v.clique[0]][0])
        for cid, d in v.diagnoses.items():
            print(f"diagnosis[{cid}]:", d)
    else:
        for d in v.disagreements:
            print("disagree:", d)
    print("informative instances:", v.informative)
    for cid in v.objectives:
        objs = [round(x, 2) if x is not None else None for x in v.objectives[cid]]
        print(f"  {cid}: obj={objs}")
        print(f"  {' ' * len(cid)}  status={v.statuses[cid]}")


if __name__ == "__main__":
    main()
