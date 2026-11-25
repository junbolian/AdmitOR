import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    bolt_length = params["bolt_length"]
    strip_lengths = [
        params["strip_length_L1"],
        params["strip_length_L2"],
        params["strip_length_L3"],
        params["strip_length_L4"],
    ]
    demands = [
        params["demand_D1"],
        params["demand_D2"],
        params["demand_D3"],
        params["demand_D4"],
    ]

    n_types = 4
    types = list(range(n_types))

    # Enumerate all feasible cutting patterns: each pattern is a tuple of
    # counts (one per strip type) whose total length does not exceed a bolt.
    patterns = []

    def build(idx, current, remaining):
        if idx == n_types:
            patterns.append(tuple(current))
            return
        max_count = int(remaining // strip_lengths[idx])
        for count in range(max_count + 1):
            current.append(count)
            build(idx + 1, current, remaining - count * strip_lengths[idx])
            current.pop()

    build(0, [], bolt_length)

    # Drop the all-zero pattern (uses a bolt for nothing).
    patterns = [p for p in patterns if sum(p) > 0]
    pattern_ids = list(range(len(patterns)))

    model = pyo.ConcreteModel()
    model.P = pyo.Set(initialize=pattern_ids)
    model.T = pyo.Set(initialize=types)

    # Number of bolts cut using each pattern.
    model.x = pyo.Var(model.P, domain=pyo.NonNegativeIntegers)

    # Objective: minimize total number of bolts used.
    model.total_bolts = pyo.Objective(
        expr=sum(model.x[p] for p in model.P), sense=pyo.minimize
    )

    # Demand satisfaction constraints.
    def demand_rule(m, t):
        return sum(patterns[p][t] * m.x[p] for p in m.P) >= demands[t]

    model.demand_con = pyo.Constraint(model.T, rule=demand_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_bolts))
    return {"objective": obj_val, "status": "optimal"}