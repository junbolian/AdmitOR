import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    cost = params["cost"]
    capacity = params["capacity"]

    n = len(supply)
    arcs = [(i, j) for i in range(n) for j in range(n) if i != j]

    model = pyo.ConcreteModel()
    model.arcs = pyo.Set(initialize=arcs, dimen=2)
    model.x = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    model.balance = pyo.Constraint(
        range(n),
        rule=lambda m, i: sum(m.x[i, j] for j in range(n) if j != i)
        - sum(m.x[j, i] for j in range(n) if j != i)
        == supply[i],
    )

    model.cap = pyo.Constraint(
        model.arcs,
        rule=lambda m, i, j: m.x[i, j] <= capacity[i][j],
    )

    model.obj = pyo.Objective(
        expr=sum(cost[i][j] * model.x[i, j] for (i, j) in arcs),
        sense=pyo.minimize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}