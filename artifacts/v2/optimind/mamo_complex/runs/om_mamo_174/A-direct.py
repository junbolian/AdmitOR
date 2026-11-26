import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    cities = [1, 2, 3, 4]
    arcs = [(i, j) for i in cities for j in cities if i != j]

    cost = {}
    for i, j in arcs:
        cost[(i, j)] = params["cost_{}_{}".format(i, j)]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(arcs, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(cost[(i, j)] * model.x[(i, j)] for i, j in arcs),
        sense=pyo.minimize,
    )

    model.out_flow = pyo.Constraint(
        cities, rule=lambda m, i: sum(m.x[(i, j)] for j in cities if j != i) == 1
    )
    model.in_flow = pyo.Constraint(
        cities, rule=lambda m, j: sum(m.x[(i, j)] for i in cities if i != j) == 1
    )

    # Subtour elimination (MTZ-style) for the single tour over 4 cities
    model.u = pyo.Var(cities, bounds=(0, 3))
    model.subtour = pyo.Constraint(
        [(i, j) for i, j in arcs if i != 1 and j != 1],
        rule=lambda m, i, j: m.u[i] - m.u[j] + 4 * m.x[(i, j)] <= 3,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}