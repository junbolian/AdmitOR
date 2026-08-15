# -*- coding: utf-8 -*-
"""AdmitOR core -- ir_extract.py (v0.4)

Extracts a base-anchored parameter-domain spec from a natural-language
problem. v0.4 adds semantic guardrails on top of syntactic validation:
  - inverted abs ranges (lo > hi): auto-swap, warn
  - degenerate ranges (lo == hi): warn
  - rel rate r outside (0, 1]: clamp to 0.3, warn
  - abs range disjoint from the base value span: replace with rel +/-30%
    around base, warn  (a domain that excludes the true values cannot test
    the model near the original problem and tends to produce infeasible,
    uninformative instantiations)
"""
import json
import re

EXTRACT_PROMPT = """You are an optimization-structure extractor. From the problem \
below, list the NUMERIC PARAMETERS (costs, prices, capacities, demands, budgets, \
coefficients) together with their ACTUAL VALUES as given in the problem data.

For each parameter also propose a perturbation domain for sensitivity testing, \
anchored at the true values: keep it physically meaningful but STRESS-TEST \
constraint activation (allow sign changes only where economically plausible, \
e.g. a net profit that may turn negative; widen enough that different \
constraints become binding). The domain must remain feasible-plausible: do not \
propose ranges that contradict the parameter's role (e.g. capacities near zero \
while demands stay large).

Index-set sizes and cardinalities (number of employees, projects, cars, ...) \
must NOT be perturbed: either OMIT them from params entirely, or freeze them \
with a degenerate abs range (lo == hi == base). Changing a size without \
resizing every dependent array produces structurally invalid instances.

Output ONLY a JSON object, no prose, exactly this schema:
{
  "params": {
    "<name>": {
      "meaning": "<short>",
      "base": <number or list of numbers, the TRUE values from the problem>,
      "perturb": {"mode": "rel", "r": <0..1>}
                 or {"mode": "abs", "lo": <num>, "hi": <num>, "integer": <bool>}\n\nIn "abs" mode, lo and hi are ABSOLUTE parameter values on the same scale as base (NOT offsets or deltas around it).
    }
  },
  "objective_sense": "max" or "min"
}

PROBLEM:
{question}
"""


def parse_json_block(text: str) -> dict:
    t = re.sub(r"^```(json)?|```$", "", text.strip(), flags=re.M).strip()
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        depth, start = 0, None
        for i, ch in enumerate(t):
            if ch == "{":
                if depth == 0:
                    start = i
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0 and start is not None:
                    return json.loads(t[start : i + 1])
        raise


def _flatten(x):
    if isinstance(x, (list, tuple)):
        for v in x:
            yield from _flatten(v)
    else:
        yield x


def _span(base):
    nums = [v for v in _flatten(base) if isinstance(v, (int, float))]
    return (min(nums), max(nums)) if nums else (None, None)


def _dims(base, acc):
    if isinstance(base, (list, tuple)):
        acc.add(len(base))
        for v in base:
            _dims(v, acc)


_SIZE_NAME = re.compile(r"(^num_|^n_|_num$|count|size|cardinal|number)", re.I)


def validate_spec(spec: dict) -> list:
    """In-place repairs; returns a list of warnings."""
    warns = []
    dims = set()
    for s in spec.values():
        _dims(s.get("base"), dims)
    for name, s in spec.items():
        p = s.get("perturb")
        if p is None:
            continue
        # Safety net behind the prompt rule: a scalar integer that matches an
        # array dimension and carries a size-like name is an index-set size;
        # perturbing it without resizing the dependent arrays produces
        # dimension-mismatched (structurally invalid) instances.
        b = s.get("base")
        if (
            isinstance(b, (int, float))
            and float(b).is_integer()
            and int(b) in dims
            and _SIZE_NAME.search(name)
        ):
            movable = (p.get("mode") == "rel" and p.get("r", 0.3) > 0) or (
                p.get("mode") == "abs" and p.get("lo") != p.get("hi")
            )
            if movable:
                s["perturb"] = {"mode": "abs", "lo": float(b), "hi": float(b), "integer": True}
                warns.append(
                    f"[{name}] looks like an index-set size (matches array "
                    f"dimension {int(b)}); frozen at base -- sizes cannot be "
                    f"perturbed without resizing dependent arrays"
                )
                continue
        if p.get("mode") == "rel":
            r = p.get("r", 0.3)
            if not (isinstance(r, (int, float)) and 0 < r <= 1):
                p["r"] = 0.3
                warns.append(f"[{name}] rel rate r={r!r} outside (0,1]; " f"clamped to 0.3")
            continue
        lo, hi = p.get("lo"), p.get("hi")
        if lo is None or hi is None:
            continue
        if lo > hi:
            p["lo"], p["hi"] = hi, lo
            lo, hi = p["lo"], p["hi"]
            warns.append(f"[{name}] inverted abs range (lo > hi); swapped")
        if lo == hi:
            warns.append(
                f"[{name}] degenerate abs range (lo == hi); " f"perturbation has no effect"
            )
        b_lo, b_hi = _span(s.get("base"))
        if b_lo is not None and (hi < b_lo or lo > b_hi):
            s["perturb"] = {"mode": "rel", "r": 0.3}
            warns.append(
                f"[{name}] abs range [{lo}, {hi}] is disjoint from "
                f"base span [{b_lo}, {b_hi}]; replaced with "
                f"rel +/-30% around base"
            )
    return warns


def _num(x):
    if isinstance(x, bool):
        return None
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def extract_spec(question: str, llm_call) -> dict:
    raw = llm_call(EXTRACT_PROMPT.replace("{question}", question))
    try:
        data = parse_json_block(raw)
    except Exception as err:
        raise ValueError(
            f"extractor output not parseable JSON ({type(err).__name__}: "
            f"{err}); likely truncated -- raise extraction max_tokens"
        ) from err
    spec = {}
    pre_warns = []
    for name, s in data.get("params", {}).items():
        if not isinstance(s, dict):
            pre_warns.append(f"[{name}] malformed param entry dropped")
            continue
        entry = {}
        if s.get("base") is not None:
            leaves = list(_flatten(s["base"]))
            if not leaves or any(_num(v) is None for v in leaves):
                pre_warns.append(f"[{name}] non-numeric base dropped")
                continue
            entry["base"] = s["base"]
        p = s.get("perturb", {"mode": "rel", "r": 0.3})
        p = p if isinstance(p, dict) else {"mode": "rel", "r": 0.3}
        mode = str(p.get("mode", "rel")).lower()
        if mode == "abs":
            lo, hi = _num(p.get("lo")), _num(p.get("hi"))
            if lo is None or hi is None:
                # e.g. per-element lists or missing bounds -- schema takes
                # scalar bounds only; keep the param via the rel fallback
                pre_warns.append(
                    f"[{name}] malformed abs bounds "
                    f"(lo/hi not scalar); fell back to rel "
                    f"+/-30% around base"
                )
                entry["perturb"] = {"mode": "rel", "r": 0.3}
            else:
                entry["perturb"] = {
                    "mode": "abs",
                    "lo": lo,
                    "hi": hi,
                    "integer": bool(p.get("integer", False)),
                }
        else:
            r = _num(p.get("r", 0.3))
            if r is None:
                pre_warns.append(f"[{name}] malformed rel r; defaulted 0.3")
                r = 0.3
            entry["perturb"] = {"mode": "rel", "r": r}
        spec[name] = entry
    warns = pre_warns + validate_spec(spec)
    return {
        "spec": spec,
        "sense": data.get("objective_sense", "max"),
        "warnings": warns,
        "raw": data,
    }
