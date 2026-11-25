import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    edges = [
        (4, 9), (3, 7), (3, 10), (5, 7), (2, 11), (1, 9), (6, 8),
        (4, 5), (4, 8), (0, 1), (0, 7), (2, 4), (10, 11), (0, 4),
        (0, 10), (2, 7), (1, 5), (6, 7), (6, 10), (4, 7), (3, 8),
        (0, 9), (8, 10), (1, 7), (2, 6)
    ]

    n_nodes = 12
    n_colors = n_nodes

    model = pyo.ConcreteModel()

    model.NODES = pyo.RangeSet(0, n_nodes - 1)
    model.COLORS = pyo.RangeSet(0, n_colors - 1)

    model.x = pyo.Var(model.NODES, model.COLORS, domain=pyo.Binary)
    model.y = pyo.Var(model.COLORS, domain=pyo.Binary)

    def assign_rule(m, i):
        return sum(m.x[i, c] for c in m.COLORS) == 1
    model.assign = pyo.Constraint(model.NODES, rule=assign_rule)

    def use_rule(m, i, c):
        return m.x[i, c] <= m.y[c]
    model.color_use = pyo.Constraint(model.NODES, model.COLORS, rule=use_rule)

    def edge_rule(m, c, i, j):
        return m.x[i, c] + m.x[j, c] <= 1
    model.conflict = pyo.Constraint(
        model.COLORS, pyo.Set(initialize=edges, dimen=2), rule=edge_rule
    )

    def sym_rule(m, c):
        if c == 0:
            return pyo.Constraint.Skip
        return m.y[c] <= m.y[c - 1]
    model.symmetry = pyo.Constraint(model.COLORS, rule=sym_rule)

    model.obj = pyo.Objective(expr=sum(model.y[c] for c in model.COLORS),
                              sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {'objective': obj_val, 'status': 'optimal'}