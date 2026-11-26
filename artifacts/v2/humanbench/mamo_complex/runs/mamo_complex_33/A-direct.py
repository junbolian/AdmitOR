import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = [1, 2, 3, 4, 5]
    arcs = [(i, j) for i in cities for j in cities if i != j]

    cost = {}
    for i, j in arcs:
        cost[(i, j)] = params["cost_{}_{}".format(i, j)]

    model = pyo.ConcreteModel()
    model.cities = pyo.Set(initialize=cities)
    model.arcs = pyo.Set(initialize=arcs, dimen=2)

    model.x = pyo.Var(model.arcs, within=pyo.Binary, initialize=0)

    # Continuous order variables for subtour elimination (MTZ)
    model.u = pyo.Var(model.cities, within=pyo.NonNegativeReals)

    def obj_rule(md):
        return sum(cost[(i, j)] * md.x[(i, j)] for (i, j) in arcs)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def out_rule(md, i):
        return sum(md.x[(i, j)] for j in cities if j != i) == 1

    def in_rule(md, j):
        return sum(md.x[(i, j)] for i in cities if i != j) == 1

    model.out_flow = pyo.Constraint(model.cities, rule=out_rule)
    model.in_flow = pyo.Constraint(model.cities, rule=in_rule)

    # MTZ subtour elimination, fix u[1] = 1
    model.u_bounds = pyo.Constraint(
        model.cities,
        rule=lambda md, i: md.u[i] == 1 if i == 1 else (md.u[i] >= 2),
    )
    model.u_upper = pyo.Constraint(
        model.cities, rule=lambda md, i: md.u[i] <= len(cities)
    )

    def mtz_rule(md, i, j):
        if i == 1 or j == 1:
            return pyo.Constraint.Skip
        return md.u[i] - md.u[j] + len(cities) * md.x[(i, j)] <= len(cities) - 1

    model.mtz = pyo.Constraint(model.arcs, rule=mtz_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}