# -*- coding: utf-8 -*-
"""AdmitOR core -- generate.py (v0.4)

Candidate generation and sandboxed execution: the LLM produces a complete
script defining solve(params); every solve runs in a subprocess (isolating
crashes, hangs and stdout pollution), with sampled parameters injected via a
temp JSON file.
"""
import json
import os
import re
import subprocess
import sys
import tempfile

from admitor.consensus import Candidate, SolveResult

CANDIDATE_PROMPT = """You are an expert in optimization modeling. Write a COMPLETE \
Python script that defines a function solve(params) which builds and solves the \
optimization problem below.

STRICT RULES:
1. Use {stack}.
2. Every numeric quantity listed in PARAMS must be read from the `params` dict \
(params["<name>"]); do NOT hardcode their values. Structural constants (set sizes, \
index structure) may be inline.
3. solve(params) must return a dict: {{"objective": <float>, "status": "optimal"}} \
on success; {{"objective": None, "status": "<short reason>"}} if infeasible/failed.
4. No printing, no file I/O, no network. Output ONLY one python code block.
5. Name the model object `model`; NEVER reuse `model` or `m` as a loop index \
or comprehension variable. Avoid Pyomo reserved attribute names for components \
(e.g. activate, deactivate, name, clone, index, display).
6. Do not wrap the whole body in a blanket try/except; let unexpected \
exceptions propagate (the harness captures them).
{strategy_extra}

PARAMS (name: meaning):
{param_desc}

PROBLEM:
{question}
"""

STRUCTURED_EXTRA = """7. Before the code, include as a Python comment a compact IR \
in JSON (sets, params, decision variables with types, constraints one line each, \
objective), then implement EXACTLY that IR."""

_CHILD = r"""
import json, sys
params = json.load(open(sys.argv[1], encoding="utf-8"))
src = open(sys.argv[2], encoding="utf-8").read()
g = {}
exec(compile(src, "candidate.py", "exec"), g)
res = g["solve"](params)
print("__ADMITOR__" + json.dumps(res, default=str))
"""


def extract_code(text: str) -> str:
    m = re.findall(r"```(?:python)?\s*(.*?)```", text, flags=re.S)
    return (m[-1] if m else text).strip()


def make_candidate(code: str, cid: str, family: str, strategy: str, timeout: int = 60) -> Candidate:
    tmpdir = tempfile.mkdtemp(prefix=f"admitor_{cid}_")
    src_path = os.path.join(tmpdir, "candidate.py")
    child_path = os.path.join(tmpdir, "child.py")
    open(src_path, "w", encoding="utf-8").write(code)
    open(child_path, "w", encoding="utf-8").write(_CHILD)

    def solve(params: dict) -> SolveResult:
        p_path = os.path.join(tmpdir, "params.json")
        json.dump(params, open(p_path, "w", encoding="utf-8"))
        try:
            out = subprocess.run(
                [sys.executable, child_path, p_path, src_path],
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding="utf-8",
                errors="replace",
            )
        except subprocess.TimeoutExpired:
            return SolveResult(None, "timeout")
        for line in (out.stdout or "").splitlines():
            if line.startswith("__ADMITOR__"):
                try:
                    d = json.loads(line[len("__ADMITOR__") :])
                    obj = d.get("objective")
                    raw_status = str(d.get("status", "unknown"))
                    # Normalize enum-ish statuses: "TerminationCondition.optimal"
                    # (any enum family) counts as optimal when a value exists.
                    tail = raw_status.split(".")[-1].strip().lower()
                    if obj is not None and tail == "optimal":
                        return SolveResult(float(obj), "optimal")
                    return SolveResult(float(obj) if obj is not None else None, raw_status)
                except Exception:
                    return SolveResult(None, "bad_output")
        err = (out.stderr or "").strip().splitlines()
        ctx = " | ".join(l.strip() for l in err[-3:])[:200] if err else "?"
        # pyomo appsi raises RuntimeError when no solution can be loaded
        # (infeasible/unbounded/limit); that is a solver verdict, not a
        # candidate bug -- keep it out of the crash bucket so error-type
        # statistics stay clean.
        if "feasible solution was not found" in ctx.lower():
            return SolveResult(None, "infeasible_or_unbounded")
        return SolveResult(None, "crash:" + ctx)

    cand = Candidate(cid, family, strategy, solve)
    cand.code = code
    return cand


def gen_candidate(
    question: str,
    param_desc: str,
    family: str,
    strategy: str,
    stack: str,
    llm_call,
    cid: str,
    probe_params: dict = None,
    retries: int = 1,
) -> Candidate:
    """llm_call(prompt) -> str, a closure routed to this family's model.

    If probe_params is given, the candidate is probed on it (the unperturbed
    base instance); on failure the same model gets one repair round with its
    own code and the failure status fed back (execution-feedback repair on
    the generation side; certification never uses this signal)."""
    prompt = CANDIDATE_PROMPT.format(
        stack=stack,
        strategy_extra=STRUCTURED_EXTRA if strategy == "structured" else "",
        param_desc=param_desc,
        question=question,
    )
    raw = llm_call(prompt)
    code = extract_code(raw)
    cand = make_candidate(code, cid, family, strategy)
    cand.raw_response, cand.code = raw, code
    if probe_params is None:
        return cand
    for _ in range(max(0, retries)):
        probe = cand.solve(probe_params)
        if probe.status == "optimal":
            break
        print(
            f"[gen] {cid}: base-instance probe failed " f"({probe.status[:120]}); one repair round"
        )
        repair = (
            prompt
            + "\n\nYOUR PREVIOUS ATTEMPT:\n```python\n"
            + code
            + "\n```\nWhen executed it failed with status: "
            + probe.status
            + "\nReturn the COMPLETE corrected script (same rules)."
        )
        raw = llm_call(repair)
        code = extract_code(raw)
        cand = make_candidate(code, cid, family, strategy)
        cand.raw_response, cand.code = raw, code
    return cand
