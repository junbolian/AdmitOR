import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n = 12
    edges = [
        (4, 9), (3, 7), (3, 10), (5, 7), (2, 11),
        (1, 9), (6, 8), (4, 5), (4, 8), (0, 1),
        (0, 7), (2, 4), (10, 11), (0, 4), (0, 10),
        (2, 7), (1, 5), (6, 7), (6, 10), (4, 7),
        (3, 8), (0, 9), (8, 10), (1, 7), (2, 6),
    ]

    num_species = params["num_species"]

    model = pyo.ConcreteModel()

    model.nodes = pyo.RangeSet(0, n - 1)
    model.colors = pyo.RangeSet(0, num_species - 1)

    model.assign = pyo.Var(model.nodes, model.colors, domain=pyo.Binary)
    model.used = pyo.Var(model.colors, domain=pyo.Binary)

    model.one_color = pyo.Constraint(
        model.nodes,
        rule=lambda m, i: sum(m.assign[i, c] for c in m.colors) == 1,
    )

    def edge_rule(m, i, j):
        return sum(m.assign[i, c] + m.assign[j, c] for c in m.colors) <= 1

    model.incompat = pyo.Constraint(
        [(i, j) for (i, j) in edges], rule=edge_rule
    )

    def used_rule(m, i, c):
        return m.assign[i, c] <= m.used[c]

    model.usage = pyo.Constraint(model.nodes, model.colors, rule=used_rule)

    model.obj = pyo.Objective(
        expr=sum(model.used[c] for c in model.colors), sense=pyo.minimize
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}