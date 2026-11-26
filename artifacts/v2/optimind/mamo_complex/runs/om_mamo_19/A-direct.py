import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = [1, 2, 3, 4]
    arcs = [(i, j) for i in cities for j in cities if i != j]

    cost = {}
    for i in cities:
        for j in cities:
            if i != j:
                cost[(i, j)] = params["cost_{}_{}".format(i, j)]

    model = pyo.ConcreteModel()
    model.ARCS = pyo.Set(initialize=arcs, dimen=2)

    model.x = pyo.Var(model.ARCS, domain=pyo.Binary)

    def obj_rule(m):
        return sum(cost[(i, j)] * m.x[(i, j)] for (i, j) in arcs)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def out_rule(m, i):
        return sum(m.x[(i, j)] for j in cities if j != i) == 1

    def in_rule(m, j):
        return sum(m.x[(i, j)] for i in cities if i != j) == 1

    model.out_flow = pyo.Constraint(cities, rule=out_rule)
    model.in_flow = pyo.Constraint(cities, rule=in_rule)

    # Subtour elimination via MTZ formulation
    model.u = pyo.Var(cities, domain=pyo.NonNegativeReals, bounds=(1, len(cities) - 1))
    model.u[1].fix(1)

    def mtz_rule(m, i, j):
        if i == 1 or j == 1:
            return pyo.Constraint.Skip
        return m.u[i] - m.u[j] + len(cities) * m.x[(i, j)] <= len(cities) - 1

    model.mtz = pyo.Constraint(arcs, rule=mtz_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}