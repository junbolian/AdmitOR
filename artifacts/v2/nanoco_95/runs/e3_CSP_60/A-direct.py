import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs
from itertools import product


def solve(params):
    bolt_length = params["bolt_length"]
    strip_lengths = params["strip_lengths"]
    demands = params["demands"]

    n_specs = len(strip_lengths)

    # Enumerate all feasible cutting patterns.
    # Upper bound for count of each spec on a bolt.
    max_counts = [int(bolt_length // L) for L in strip_lengths]
    patterns = []
    for counts in product(*[range(c + 1) for c in max_counts]):
        if sum(c * L for c, L in zip(counts, strip_lengths)) <= bolt_length:
            if sum(counts) >= 1:
                patterns.append(counts)

    n_patterns = len(patterns)

    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, n_patterns - 1)
    model.S = pyo.RangeSet(0, n_specs - 1)

    model.x = pyo.Var(model.P, domain=pyo.NonNegativeIntegers)

    def obj_rule(m):
        return sum(m.x[p] for p in m.P)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(m, s):
        return sum(patterns[p][s] * m.x[p] for p in m.P) >= demands[s]
    model.demand_con = pyo.Constraint(model.S, rule=demand_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}