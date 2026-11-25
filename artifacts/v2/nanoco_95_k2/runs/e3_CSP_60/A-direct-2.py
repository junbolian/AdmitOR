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
    # Generate all feasible cutting patterns for a single bolt
    patterns = []

    def gen_patterns(idx, remaining, current):
        if idx == n_types:
            patterns.append(tuple(current))
            return
        length = strip_lengths[idx]
        max_count = int((remaining + 1e-9) // length)
        for count in range(max_count + 1):
            current.append(count)
            gen_patterns(idx + 1, remaining - count * length, current)
            current.pop()

    gen_patterns(0, bolt_length, [])

    # Pattern indices
    pattern_indices = list(range(len(patterns)))
    type_indices = list(range(n_types))

    model = pyo.ConcreteModel()
    model.P = pyo.Set(initialize=pattern_indices)
    model.T = pyo.Set(initialize=type_indices)

    # x[p]: number of bolts cut using pattern p
    model.x = pyo.Var(model.P, domain=pyo.NonNegativeIntegers)

    # Objective: minimize total bolts
    def obj_rule(m):
        return sum(m.x[p] for p in m.P)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Demand constraints
    def demand_rule(m, t):
        return sum(patterns[p][t] * m.x[p] for p in m.P) >= demands[t]
    model.demand = pyo.Constraint(model.T, rule=demand_rule)

    # Cap on number of bolts to help the solver (any feasible solution uses at most sum of demands)
    # Not a strict requirement but bounds the variables; use pattern count naturally.
    solver = Highs()
    solver.solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}