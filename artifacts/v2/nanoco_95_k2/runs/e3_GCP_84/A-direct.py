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

    model = pyo.ConcreteModel()
    model.V = pyo.RangeSet(0, n - 1)
    model.K = pyo.RangeSet(0, n - 1)

    model.x = pyo.Var(model.V, model.K, domain=pyo.Binary)
    model.y = pyo.Var(model.K, domain=pyo.Binary)

    model.obj = pyo.Objective(expr=sum(model.y[k] for k in model.K), sense=pyo.minimize)

    model.assign = pyo.Constraint(model.V, rule=lambda m, v: sum(m.x[v, k] for k in m.K) == 1)

    def link_rule(m, v, w):
        return sum(m.x[v, k] + m.x[w, k] for k in m.K) <= 1
    model.link = pyo.Constraint(edges, rule=link_rule)

    def use_rule(m, v, k):
        return m.x[v, k] <= m.y[k]
    model.use = pyo.Constraint(model.V, model.K, rule=use_rule)

    # symmetry breaking: y is non-increasing, and node k is only allowed
    # to use color k if colors 0..k-1 are already in use (anchored ordering)
    def order_rule(m, k):
        if k < n - 1:
            return m.y[k + 1] <= m.y[k]
        return pyo.Constraint.Skip
    model.order = pyo.Constraint(model.K, rule=order_rule)

    # require each of the first few colors to be used by its anchor node,
    # i.e., node k uses color k when color k is active -> ties colors to nodes
    def anchor_rule(m, v, k):
        if v == k:
            return pyo.Constraint.Skip
        return m.x[v, k] <= m.y[k]
    model.anchor = pyo.Constraint(model.V, model.K, rule=anchor_rule)

    def sym_break(m, v, k):
        # node v cannot use color k if v < k (prevents trivially permuted solutions)
        if v < k:
            return m.x[v, k] == 0
        return pyo.Constraint.Skip
    model.sym = pyo.Constraint(model.V, model.K, rule=sym_break)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}