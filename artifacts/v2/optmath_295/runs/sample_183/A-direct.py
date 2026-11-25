import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = list(range(8))
    n = 8

    dist = {}
    for i in cities:
        for j in cities:
            if i != j:
                dist[(i, j)] = params["dist_%d_%d" % (i, j)]

    model = pyo.ConcreteModel()

    model.x = pyo.Var([(i, j) for i in cities for j in cities if i != j], domain=pyo.Binary)
    model.u = pyo.Var(cities, domain=pyo.NonNegativeReals, bounds=(0, n - 1))

    model.u[0].fix(0)

    model.obj = pyo.Objective(
        expr=sum(dist[(i, j)] * model.x[(i, j)] for (i, j) in dist),
        sense=pyo.minimize,
    )

    def out_rule(m, i):
        return sum(m.x[(i, j)] for j in cities if j != i) == 1

    def in_rule(m, j):
        return sum(m.x[(i, j)] for i in cities if i != j) == 1

    model.out_cons = pyo.Constraint(cities, rule=out_rule)
    model.in_cons = pyo.Constraint(cities, rule=in_rule)

    def subtour_rule(m, i, j):
        if i != j and i != 0 and j != 0:
            return m.u[i] - m.u[j] + n * m.x[(i, j)] <= n - 1
        return pyo.Constraint.Skip

    model.subtour_cons = pyo.Constraint(
        [(i, j) for i in cities for j in cities if i != j], rule=subtour_rule
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}