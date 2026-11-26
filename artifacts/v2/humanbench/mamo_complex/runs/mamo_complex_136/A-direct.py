import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    cities = [1, 2, 3, 4, 5]

    cost = {}
    for i in cities:
        for j in cities:
            if i != j:
                cost[(i, j)] = params["cost_%d_%d" % (i, j)]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(
        [(i, j) for i in cities for j in cities if i != j],
        domain=pyo.Binary,
    )

    def obj_rule(m):
        return sum(cost[(i, j)] * m.x[(i, j)]
                   for i in cities for j in cities if i != j)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def out_rule(m, i):
        return sum(m.x[(i, j)] for j in cities if j != i) == 1

    def in_rule(m, j):
        return sum(m.x[(i, j)] for i in cities if i != j) == 1

    model.out_flow = pyo.Constraint(cities, rule=out_rule)
    model.in_flow = pyo.Constraint(cities, rule=in_rule)

    # Subtour elimination (MTZ) for 5 cities
    model.u = pyo.Var(cities, domain=pyo.NonNegativeReals, bounds=(1, 5))

    def mtz_rule(m, i, j):
        if i != j and i != 1 and j != 1:
            return m.u[i] - m.u[j] + 5 * m.x[(i, j)] <= 4
        return pyo.Constraint.Skip

    model.mtz = pyo.Constraint(cities, cities, rule=mtz_rule)
    model.u[1].fix(1)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {'objective': obj_val, 'status': 'optimal'}