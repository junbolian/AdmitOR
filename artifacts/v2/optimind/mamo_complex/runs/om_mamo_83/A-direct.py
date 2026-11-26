import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    shops = [1, 2, 3, 4, 5]

    cost = {}
    for i in shops:
        for j in shops:
            if i != j:
                cost[(i, j)] = params["cost_{}_{}".format(i, j)]

    model = pyo.ConcreteModel()
    model.SHOPS = pyo.Set(initialize=shops)
    model.ARCS = pyo.Set(initialize=list(cost.keys()), dimen=2, within=model.SHOPS * model.SHOPS)

    model.x = pyo.Var(model.ARCS, domain=pyo.Binary)

    def obj_rule(mod):
        return sum(cost[(i, j)] * mod.x[(i, j)] for (i, j) in cost)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def out_rule(mod, i):
        return sum(mod.x[(i, j)] for j in shops if j != i) == 1

    def in_rule(mod, j):
        return sum(mod.x[(i, j)] for i in shops if i != j) == 1

    model.out_con = pyo.Constraint(model.SHOPS, rule=out_rule)
    model.in_con = pyo.Constraint(model.SHOPS, rule=in_rule)

    # Subtour elimination (MTZ) to ensure a single tour.
    model.u = pyo.Var(model.SHOPS, bounds=(1, len(shops)))
    model.u[1].fix(1)

    def mtz_rule(mod, i, j):
        if i != j and i != 1 and j != 1:
            return mod.u[i] - mod.u[j] + len(shops) * mod.x[(i, j)] <= len(shops) - 1
        return pyo.Constraint.Skip

    model.mtz_con = pyo.Constraint(model.SHOPS, model.SHOPS, rule=mtz_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}