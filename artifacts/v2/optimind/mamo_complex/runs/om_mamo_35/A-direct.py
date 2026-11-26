import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cities = [1, 2, 3, 4, 5, 6]

    cost = {}
    for i in cities:
        for j in cities:
            if i == j:
                continue
            a, b = min(i, j), max(i, j)
            cost[(i, j)] = params["cost_{}_{}".format(a, b)]

    arcs = [(i, j) for i in cities for j in cities if i != j]

    model = pyo.ConcreteModel()
    model.x = pyo.Var(arcs, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(cost[(i, j)] * model.x[(i, j)] for (i, j) in arcs),
        sense=pyo.minimize,
    )

    # Each city has exactly one outgoing arc
    model.out_flow = pyo.Constraint(
        cities,
        rule=lambda m, i: sum(m.x[(i, j)] for j in cities if j != i) == 1,
    )

    # Each city has exactly one incoming arc
    model.in_flow = pyo.Constraint(
        cities,
        rule=lambda m, j: sum(m.x[(i, j)] for i in cities if i != j) == 1,
    )

    # Subtour elimination (MTZ) with auxiliary order variables
    model.u = pyo.Var(cities, domain=pyo.NonNegativeReals, bounds=(1, len(cities)))
    model.mtz = pyo.Constraint(
        [(i, j) for (i, j) in arcs if i != 1 and j != 1],
        rule=lambda m, i, j: m.u[i] - m.u[j] + len(cities) * m.x[(i, j)]
        <= len(cities) - 1,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}