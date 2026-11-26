import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    d12 = params["d12"]
    d21 = params["d21"]
    c11 = params["c11"]
    c12 = params["c12"]
    c21 = params["c21"]
    c22 = params["c22"]

    n = 2
    factories = list(range(n))
    locations = list(range(n))

    d = {(0, 1): d12, (1, 0): d21}
    c = {(0, 0): c11, (0, 1): c12, (1, 0): c21, (1, 1): c22}

    pairs = [(i, j) for i in factories for j in factories if i != j]

    model = pyo.ConcreteModel()

    model.F = pyo.Set(initialize=factories)
    model.L = pyo.Set(initialize=locations)
    model.P = pyo.Set(initialize=pairs, dimen=2)

    model.x = pyo.Var(model.F, model.L, domain=pyo.Binary)
    model.y = pyo.Var(model.P, model.L, model.L, domain=pyo.Binary)

    model.assign_con = pyo.Constraint(
        model.F, rule=lambda m, i: sum(m.x[i, p] for p in m.L) == 1
    )
    model.loc_con = pyo.Constraint(
        model.L, rule=lambda m, p: sum(m.x[i, p] for i in m.F) == 1
    )

    def link_rule(m, i, j, p, q):
        return m.y[i, j, p, q] == m.x[i, p] * m.x[j, q]

    model.link_con = pyo.Constraint(model.P, model.L, model.L, rule=link_rule)

    def cost_rule(m):
        return sum(
            d[i, j] * c[p, q] * m.y[i, j, p, q]
            for (i, j) in m.P
            for p in m.L
            for q in m.L
        )

    model.obj = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}