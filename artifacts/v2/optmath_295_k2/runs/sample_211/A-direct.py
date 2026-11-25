import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    cities = [0, 1, 2, 3, 4]
    n = len(cities)
    arcs = [(i, j) for i in cities for j in cities if i != j]

    cost = {(i, j): params["cost_%d_%d" % (i, j)] for (i, j) in arcs}

    model = pyo.ConcreteModel()

    model.x = pyo.Var(arcs, domain=pyo.Binary)
    model.u = pyo.Var(cities, domain=pyo.NonNegativeReals)

    model.obj = pyo.Objective(
        expr=sum(cost[i, j] * model.x[i, j] for (i, j) in arcs),
        sense=pyo.minimize,
    )

    model.out_deg = pyo.Constraint(
        cities,
        rule=lambda m, i: sum(m.x[i, j] for j in cities if j != i) == 1,
    )
    model.in_deg = pyo.Constraint(
        cities,
        rule=lambda m, j: sum(m.x[i, j] for i in cities if i != j) == 1,
    )

    model.u_lower = pyo.Constraint(
        cities,
        rule=lambda m, i: m.u[i] >= 0,
    )
    model.u_upper = pyo.Constraint(
        cities,
        rule=lambda m, i: m.u[i] <= n - 1,
    )

    model.subtour = pyo.Constraint(
        [(i, j) for (i, j) in arcs if i != 0 and j != 0],
        rule=lambda m, i, j: m.u[i] - m.u[j] + n * m.x[i, j] <= n - 1,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}