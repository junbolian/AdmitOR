import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    seg_lengths = params["segment_lengths"]
    seg_demands = params["segment_demands"]
    L = params["standard_rebar_length"]

    n_types = len(seg_lengths)

    # Max number of pieces of any type on a single rebar (only used to bound count vars)
    max_pieces = max(int(L // seg_lengths[i]) for i in range(n_types))

    # Enumerate all maximal cutting patterns: a pattern is (count per type, total length)
    # We only need patterns that are not dominated; but we keep all feasible patterns.
    patterns = []

    def generate(idx, current, remaining):
        if idx == n_types:
            if sum(current) > 0:
                patterns.append(tuple(current))
            return
        max_k = int(remaining // seg_lengths[idx])
        for k in range(max_k + 1):
            current.append(k)
            generate(idx + 1, current, remaining - k * seg_lengths[idx])
            current.pop()

    generate(0, [], L)

    # Bound on number of standard rebars: a trivial upper bound is sum of demands
    upper_bound = sum(seg_demands)

    model = pyo.ConcreteModel()

    n_patterns = len(patterns)
    model.P = pyo.RangeSet(0, n_patterns - 1)
    model.T = pyo.RangeSet(0, n_types - 1)

    # Pattern usage counts (number of standard rebars cut with pattern p)
    model.use = pyo.Var(model.P, domain=pyo.NonNegativeIntegers, bounds=(0, upper_bound))

    # Demand constraints: total pieces of each type must equal the demand
    def demand_rule(m, i):
        return sum(patterns[p][i] * m.use[p] for p in range(n_patterns)) == seg_demands[i]
    model.demand = pyo.Constraint(model.T, rule=demand_rule)

    # Objective: minimize total number of standard rebars used
    model.obj = pyo.Objective(
        expr=sum(model.use[p] for p in range(n_patterns)),
        sense=pyo.minimize,
    )

    solver = Highs()
    solver.solve(model)

    try:
        obj_val = float(pyo.value(model.obj))
    except Exception:
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}