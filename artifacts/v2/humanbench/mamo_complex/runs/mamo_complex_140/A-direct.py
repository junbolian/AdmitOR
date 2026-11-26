import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["cost_matrix"]
    n = len(cost)
    cities = list(range(n))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(cities, cities, domain=pyo.Binary, initialize=0)
    model.arcs = pyo.Set(initialize=[(i, j) for i in cities for j in cities if i != j])

    def obj_rule(mdl):
        return sum(cost[i][j] * mdl.x[i, j] for (i, j) in mdl.arcs)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def out_rule(mdl, i):
        return sum(mdl.x[i, j] for j in cities if j != i) == 1

    model.out_cons = pyo.Constraint(cities, rule=out_rule)

    def in_rule(mdl, j):
        return sum(mdl.x[i, j] for i in cities if i != j) == 1

    model.in_cons = pyo.Constraint(cities, rule=in_rule)

    model.u = pyo.Var(cities, domain=pyo.NonNegativeReals, bounds=(0, n - 1))
    for i in cities:
        model.u[i].setlb(1)
        model.u[i].setub(n - 1)
    model.u[0].setlb(0)
    model.u[0].setub(0)

    def mtz_rule(mdl, i, j):
        if i != j and i != 0 and j != 0:
            return mdl.u[i] - mdl.u[j] + (n - 1) * mdl.x[i, j] <= n - 2
        return pyo.Constraint.Skip

    model.mtz_cons = pyo.Constraint(cities, cities, rule=mtz_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}