import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = [1, 2, 3, 4, 5]
    n = len(cities)
    arcs = [(i, j) for i in cities for j in cities if i != j]

    cost = {}
    for i in cities:
        for j in cities:
            if i != j:
                cost[(i, j)] = params[f"cost_{i}_{j}"]

    model = pyo.ConcreteModel()

    model.arcs = pyo.Set(initialize=arcs, dimen=2)
    model.cities = pyo.Set(initialize=cities)

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)
    model.u = pyo.Var(model.cities, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(cost[(i, j)] * m.x[(i, j)] for (i, j) in arcs)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def out_rule(m, i):
        return sum(m.x[(i, j)] for j in cities if j != i) == 1

    def in_rule(m, j):
        return sum(m.x[(i, j)] for i in cities if i != j) == 1

    model.out_cons = pyo.Constraint(model.cities, rule=out_rule)
    model.in_cons = pyo.Constraint(model.cities, rule=in_rule)

    model.u[1].fix(1)

    def mtz_rule(m, i, j):
        if i != 1 and j != 1 and i != j:
            return m.u[i] - m.u[j] + (n - 1) * m.x[(i, j)] <= n - 2
        return pyo.Constraint.Skip

    model.mtz = pyo.Constraint(model.arcs, rule=mtz_rule)

    def u_bound_rule(m, i):
        return m.u[i] <= n

    model.u_bound = pyo.Constraint(model.cities, rule=u_bound_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}