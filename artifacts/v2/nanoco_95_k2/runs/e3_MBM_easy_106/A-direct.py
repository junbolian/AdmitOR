import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    edges = [
        (0, 1), (0, 2),
        (1, 0), (1, 3),
        (2, 2), (2, 3),
        (3, 1), (3, 2), (3, 3), (3, 4),
        (4, 0), (4, 1),
        (5, 3),
    ]
    farms = list(range(7))
    subs = list(range(5))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(edges, domain=pyo.Binary)

    def obj_rule(m):
        return sum(m.x[i, j] for (i, j) in edges)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def farm_rule(m, i):
        outgoing = [(a, j) for (a, j) in edges if a == i]
        if not outgoing:
            return pyo.Constraint.Skip
        return sum(m.x[a, j] for (a, j) in outgoing) <= 1

    model.farm_limit = pyo.Constraint(farms, rule=farm_rule)

    def sub_rule(m, j):
        incoming = [(i, b) for (i, b) in edges if b == j]
        if not incoming:
            return pyo.Constraint.Skip
        return sum(m.x[i, b] for (i, b) in incoming) <= 1

    model.sub_limit = pyo.Constraint(subs, rule=sub_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}