import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    bandwidth = params["bandwidth"]  # list of 8 bandwidths
    n = len(bandwidth)

    edges = [(0, 1), (2, 4), (2, 7), (3, 7), (1, 4), (2, 3), (0, 5), (2, 5), (3, 5)]

    total = sum(bandwidth)

    model = pyo.ConcreteModel()

    model.TOWERS = pyo.RangeSet(0, n - 1)
    model.PAIRS = pyo.Set(initialize=edges, dimen=2)

    # Big-M: a valid upper bound on the max span
    M = total

    model.start = pyo.Var(model.TOWERS, domain=pyo.NonNegativeReals)

    # max index used (span)
    model.span = pyo.Var(domain=pyo.NonNegativeReals)

    # Binary for each interfering pair: y=1 means i is entirely before j
    model.before = pyo.Var(model.PAIRS, domain=pyo.Binary)

    # span >= end of each tower
    def span_con(m, i):
        return m.span >= m.start[i] + bandwidth[i]
    model.span_con = pyo.Constraint(model.TOWERS, rule=span_con)

    # Disjunctive constraints for each interfering pair (i, j):
    #   i before j: start[j] >= start[i] + b[i]
    #   j before i: start[i] >= start[j] + b[j]
    def disj1(m, i, j):
        return m.start[j] >= m.start[i] + bandwidth[i] - M * (1 - m.before[i, j])
    model.disj1 = pyo.Constraint(model.PAIRS, rule=disj1)

    def disj2(m, i, j):
        return m.start[i] >= m.start[j] + bandwidth[j] - M * m.before[i, j]
    model.disj2 = pyo.Constraint(model.PAIRS, rule=disj2)

    model.obj = pyo.Objective(expr=model.span, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}