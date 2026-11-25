import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    n_vars = 10
    n_regs = 10
    edges = [
        (5, 8),
        (4, 9),
        (3, 7),
        (0, 3),
        (1, 4),
        (2, 3),
        (6, 7),
        (4, 5),
        (3, 9),
        (5, 9),
        (6, 9),
    ]

    model = pyo.ConcreteModel()
    model.V = pyo.RangeSet(0, n_vars - 1)
    model.R = pyo.RangeSet(0, n_regs - 1)

    model.x = pyo.Var(model.V, model.R, domain=pyo.Binary)
    model.y = pyo.Var(model.R, domain=pyo.Binary)

    def assign_rule(m, v):
        return sum(m.x[v, r] for r in m.R) == 1
    model.assign = pyo.Constraint(model.V, rule=assign_rule)

    def link_rule(m, v, r):
        return m.x[v, r] <= m.y[r]
    model.link = pyo.Constraint(model.V, model.R, rule=link_rule)

    def conflict_rule(m, i, j):
        return sum(r * m.x[i, r] for r in m.R) != sum(r * m.x[j, r] for r in m.R)
    # Use binary indicator-based distinctness
    model.c1 = pyo.ConstraintList()
    for (i, j) in edges:
        for r in range(n_regs):
            model.c1.add(model.x[i, r] + model.x[j, r] <= 1)

    model.obj = pyo.Objective(expr=sum(model.y[r] for r in model.R), sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}