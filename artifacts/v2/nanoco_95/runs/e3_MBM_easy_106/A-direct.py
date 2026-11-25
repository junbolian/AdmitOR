import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    farms = range(7)
    substations = range(5)
    edges = [
        (0, 1), (0, 2),
        (1, 0), (1, 3),
        (2, 2), (2, 3),
        (3, 1), (3, 2), (3, 3), (3, 4),
        (4, 0), (4, 1),
        (5, 3),
    ]

    edges_by_farm = {i: [e for e in edges if e[0] == i] for i in farms}
    edges_by_sub = {j: [e for e in edges if e[1] == j] for j in substations}

    model = pyo.ConcreteModel()
    model.x = pyo.Var(edges, domain=pyo.Binary)

    def farm_rule(model, i):
        es = edges_by_farm[i]
        if not es:
            return pyo.Constraint.Skip
        return sum(model.x[e] for e in es) <= 1

    def sub_rule(model, j):
        es = edges_by_sub[j]
        if not es:
            return pyo.Constraint.Skip
        return sum(model.x[e] for e in es) <= 1

    model.farm_limit = pyo.Constraint(farms, rule=farm_rule)
    model.sub_limit = pyo.Constraint(substations, rule=sub_rule)

    model.obj = pyo.Objective(expr=sum(model.x[e] for e in edges), sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}