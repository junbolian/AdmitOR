import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n = 12
    edges = [
        (0, 1), (0, 4), (5, 8), (4, 9), (6, 9), (6, 8),
        (3, 10), (5, 7), (0, 6), (6, 7), (8, 9), (2, 6),
        (0, 5), (9, 11), (0, 8), (2, 11), (0, 11),
    ]

    model = pyo.ConcreteModel()
    model.nodes = pyo.RangeSet(0, n - 1)
    model.colors = pyo.RangeSet(0, n - 1)

    model.x = pyo.Var(model.nodes, model.colors, domain=pyo.Binary)
    model.w = pyo.Var(model.colors, domain=pyo.Binary)

    def one_color_rule(m, v):
        return sum(m.x[v, c] for c in m.colors) == 1

    def edge_rule(m, u, v, c):
        return m.x[u, c] + m.x[v, c] <= 1

    def obj_rule(m):
        return sum(m.w[c] for c in m.colors)

    def link_rule(m, v, c):
        return m.x[v, c] <= m.w[c]

    model.one_color = pyo.Constraint(model.nodes, rule=one_color_rule)
    model.edge_conflict = pyo.Constraint(
        [(u, v, c) for (u, v) in edges for c in range(n)], rule=edge_rule
    )
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)
    model.link = pyo.Constraint(
        [(v, c) for v in range(n) for c in range(n)], rule=link_rule
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}