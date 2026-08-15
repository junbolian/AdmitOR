# -*- coding: utf-8 -*-
"""Regression tests for nested-list sampling and spec validation.

Checkpoints, keeping the labels used during development:
  T1  matrix-base specs sample without crashing and preserve shape exactly.
  T2  RNG backward compatibility: for scalar and flat-list rel specs the
      draw sequence is identical to the pre-nesting implementation, so every
      already-vaulted run reproduces byte for byte.
  T3  End-to-end run_l3 with a matrix param: a correct model against one
      that ignores the assignment-limit matrix. The wrong one must be
      excluded and its diagnosis line must render (this exercises _short on
      matrices).
  T4  Index-set size parameters are frozen by validate_spec, matrix shape is
      stable across samples, a dimension-coincident non-size parameter is
      left perturbable (T4b), and an already-degenerate size keeps its
      warning without being double-frozen (T4c).
  T5  Solver-status normalization: a Pyomo appsi no-solution RuntimeError is
      classified as infeasible_or_unbounded rather than a crash, while a
      genuine candidate bug still lands in the crash bucket.

Runs fully offline. T5 spawns subprocesses through the candidate sandbox but
never touches the network.
"""
import random

from admitor.consensus import Candidate, SolveResult, _sample_one, run_l3, sample_params
from admitor.generate import make_candidate
from admitor.ir_extract import validate_spec

DEV4_SPEC = {
    "employee_availability": {"base": [7, 11, 10, 9, 9, 12], "perturb": {"mode": "rel", "r": 0.2}},
    "project_requirements": {"base": [8, 12, 9, 9, 10, 10], "perturb": {"mode": "rel", "r": 0.15}},
    "cost_matrix": {
        "base": [
            [22, 19, 19, 26, 26, 25],
            [20, 25, 17, 29, 21, 19],
            [30, 23, 30, 22, 20, 29],
            [30, 24, 27, 28, 23, 15],
            [23, 27, 22, 15, 18, 27],
            [25, 17, 16, 21, 30, 16],
        ],
        "perturb": {"mode": "rel", "r": 0.3},
    },
    "assignment_limits": {
        "base": [
            [8, 5, 4, 5, 7, 4],
            [6, 6, 8, 5, 6, 6],
            [6, 8, 4, 4, 4, 7],
            [7, 7, 8, 4, 7, 5],
            [5, 5, 8, 5, 6, 8],
            [4, 6, 6, 4, 4, 4],
        ],
        "perturb": {"mode": "rel", "r": 0.25},
    },
    # structural sizes: degenerate abs freeze, integer
    "num_employees": {"base": 8, "perturb": {"mode": "abs", "lo": 8.0, "hi": 8.0, "integer": True}},
}


def shape(x):
    if isinstance(x, list):
        return [shape(v) for v in x]
    return 0


def test_t1_matrix_specs_sample_shape_preserving():
    """T1: matrix specs sample crash-free and shape-preserving."""
    rng = random.Random(42)
    for _ in range(5):
        p = sample_params(DEV4_SPEC, rng)
        for k in DEV4_SPEC:
            assert shape(p[k]) == shape(DEV4_SPEC[k]["base"]), f"shape lost: {k}"
        assert p["num_employees"] == 8 and isinstance(p["num_employees"], int)
        flat = [v for row in p["cost_matrix"] for v in row]
        base = [v for row in DEV4_SPEC["cost_matrix"]["base"] for v in row]
        assert all(0.69 * b <= v <= 1.31 * b for v, b in zip(flat, base))


def _old_sample_one(base, mode_cfg, rng):
    """Verbatim pre-nesting implementation, kept as the reference draw
    sequence T2 compares against."""
    if mode_cfg["mode"] == "rel":
        r = mode_cfg.get("r", 0.3)
        if isinstance(base, (list, tuple)):
            return [b * rng.uniform(1 - r, 1 + r) for b in base]
        return base * rng.uniform(1 - r, 1 + r)
    lo, hi = sorted((mode_cfg["lo"], mode_cfg["hi"]))
    n = len(base) if isinstance(base, (list, tuple)) else 1
    vals = [rng.uniform(lo, hi) for _ in range(n)]
    if mode_cfg.get("integer"):
        vals = [round(v) for v in vals]
    return vals if n > 1 else vals[0]


def test_t2_rng_backward_compatible():
    """T2: scalar and flat-list draws identical to the previous version."""
    cases = [
        (304, {"mode": "rel", "r": 0.2}),
        ([15, 17, 16], {"mode": "rel", "r": 0.3}),
        (5, {"mode": "abs", "lo": 3, "hi": 9, "integer": False}),
        ([1, 2, 3, 4], {"mode": "abs", "lo": 0, "hi": 10, "integer": True}),
    ]
    r1, r2 = random.Random(42), random.Random(42)
    for base, cfg in cases:
        a, b = _old_sample_one(base, cfg, r1), _sample_one(base, cfg, r2)
        assert a == b, f"RNG sequence drifted on {base} {cfg}: {a} vs {b}"
    assert r1.random() == r2.random(), "post-call RNG states differ"


def _make_solver(respect_limits):
    def solve(p):
        # Toy assignment: greedily meet each project's requirement from the
        # cheapest employees, applying the per-cell cap only if respect_limits.
        m, n = len(p["employee_availability"]), len(p["project_requirements"])
        avail = list(p["employee_availability"])
        total = 0.0
        for j in range(n):
            need = p["project_requirements"][j]
            order = sorted(range(m), key=lambda i: p["cost_matrix"][i][j])
            for i in order:
                if need <= 0:
                    break
                cap = p["assignment_limits"][i][j] if respect_limits else 1e9
                x = min(need, avail[i], cap)
                total += x * p["cost_matrix"][i][j]
                avail[i] -= x
                need -= x
            if need > 1e-9:
                return SolveResult(None, "infeasible")
        return SolveResult(total, "optimal")

    return solve


def test_t3_end_to_end_matrix_run_l3():
    """T3: the model ignoring the limits matrix is excluded, with a rendered
    diagnosis."""
    spec3 = {k: v for k, v in DEV4_SPEC.items() if k != "num_employees"}
    cands = [
        Candidate("A-direct", "deepseek", "direct", _make_solver(True)),
        Candidate("B-structured", "gpt", "structured", _make_solver(True)),
        Candidate("G-nolimit", "claude", "direct", _make_solver(False)),
    ]
    v = run_l3(cands, spec3, m=5, seed=42)
    assert v.decision == "ACCEPT", v.decision
    assert set(v.clique) == {"A-direct", "B-structured"}
    assert "G-nolimit" in v.diagnoses
    assert "diverges" in v.diagnoses["G-nolimit"] or "failed" in v.diagnoses["G-nolimit"]


def test_t4_index_set_sizes_frozen():
    """T4: size params frozen, matrix shape stable across samples."""
    dev5 = {
        "preference_matrix": {
            "base": [
                [0, 0, 0, 0, 1, 0],
                [0, 1, 0, 0, 0, 0],
                [0, 0, 1, 1, 1, 0],
                [0, 0, 0, 0, 0, 1],
                [0, 0, 0, 0, 0, 0],
                [1, 0, 0, 0, 0, 0],
                [0, 0, 0, 0, 0, 0],
            ],
            "perturb": {"mode": "abs", "lo": 0.0, "hi": 1.0, "integer": True},
        },
        "num_participants": {
            "base": 7,
            "perturb": {"mode": "abs", "lo": 5.0, "hi": 9.0, "integer": True},
        },
        "num_cars": {"base": 6, "perturb": {"mode": "abs", "lo": 4.0, "hi": 8.0, "integer": True}},
    }
    w = validate_spec(dev5)
    assert dev5["num_participants"]["perturb"]["lo"] == 7.0
    assert dev5["num_participants"]["perturb"]["hi"] == 7.0
    assert dev5["num_cars"]["perturb"] == {"mode": "abs", "lo": 6.0, "hi": 6.0, "integer": True}
    assert sum("index-set size" in x for x in w) == 2, w
    # preference_matrix itself untouched (list base, still perturbable)
    assert dev5["preference_matrix"]["perturb"]["hi"] == 1.0
    rng = random.Random(42)
    for _ in range(10):
        p = sample_params(dev5, rng)
        assert p["num_participants"] == 7 and p["num_cars"] == 6
        assert len(p["preference_matrix"]) == 7
        assert all(len(row) == 6 for row in p["preference_matrix"])
        assert all(v in (0, 1) for row in p["preference_matrix"] for v in row)


def test_t4b_dimension_coincident_non_size_left_perturbable():
    """T4b: a non-size scalar that happens to equal a dimension is not
    frozen."""
    tricky = {
        "budget": {"base": 6, "perturb": {"mode": "abs", "lo": 4.0, "hi": 9.0, "integer": True}},
        "costs": {"base": [1, 2, 3, 4, 5, 6], "perturb": {"mode": "rel", "r": 0.2}},
    }
    w2 = validate_spec(tricky)
    assert tricky["budget"]["perturb"]["hi"] == 9.0, tricky
    assert not any("index-set size" in x for x in w2)


def test_t4c_pre_frozen_size_not_double_frozen():
    """T4c: an already-degenerate size keeps the degenerate warning and is
    not frozen twice."""
    dev2ish = {
        "num_employees": {
            "base": 8,
            "perturb": {"mode": "abs", "lo": 8.0, "hi": 8.0, "integer": True},
        },
        "avail": {"base": [0, 7, 16, 19, 16, 15, 19, 20], "perturb": {"mode": "rel", "r": 0.3}},
    }
    w3 = validate_spec(dev2ish)
    assert any("degenerate" in x for x in w3)
    assert not any("index-set" in x for x in w3), w3


def test_t5_solver_status_normalization():
    """T5: appsi no-solution normalized; real bugs still crash."""
    code_crash = """
def solve(params):
    raise RuntimeError("A feasible solution was not found, so no solution "
                       "can be loaded.")
"""
    c = make_candidate(code_crash, "T5", "gpt", "direct", timeout=30)
    r = c.solve({})
    assert r.status == "infeasible_or_unbounded", r.status

    code_bug = """
def solve(params):
    return {"objective": [1][5], "status": "optimal"}
"""
    c2 = make_candidate(code_bug, "T5b", "gpt", "direct", timeout=30)
    r2 = c2.solve({})
    assert r2.status.startswith("crash:"), r2.status
