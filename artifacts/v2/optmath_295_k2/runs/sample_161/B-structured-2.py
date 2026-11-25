# IR: {"sets":{"V":[0,1,2,3,4,5,6],"N":"V excluding 0","A":"{(i,j) in V x V: i != j}","B":"{(i,j) in N x N: i != j}"},"params":{"c[i,j]":"params[f'cost_{i}_{j}'] for each (i,j) in A"},"variables":{"x[i,j]":"binary for (i,j) in A","u[i]":"integer in [0,6] for i in V"},"constraints":["sum(x[i,j] for j in V if j != i) = 1 for i in V","sum(x[i,j] for i in V if i != j) = 1 for j in V","u[0] = 0","u[i] - u[j] + 7*x[i,j] <= 6 for (i,j) in B"],"objective":"minimize sum(c[i,j]*x[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.V = pyo.Set(initialize=range(7), ordered=True)
    model.N = pyo.Set(initialize=range(1, 7), ordered=True)
    model.A = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(7)
            for j in range(7)
            if i != j
        ],
    )
    model.B = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(1, 7)
            for j in range(1, 7)
            if i != j
        ],
    )

    model.travel_cost = pyo.Param(
        model.A,
        initialize={
            (i, j): params[f"cost_{i}_{j}"]
            for i, j in model.A
        },
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.A, domain=pyo.Binary)
    model.u = pyo.Var(model.V, domain=pyo.Integers, bounds=(0, 6))
    model.u[0].fix(0)

    def departure_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.V if j != i) == 1

    model.departure = pyo.Constraint(model.V, rule=departure_rule)

    def arrival_rule(mdl, j):
        return sum(mdl.x[i, j] for i in mdl.V if i != j) == 1

    model.arrival = pyo.Constraint(model.V, rule=arrival_rule)

    def subtour_rule(mdl, i, j):
        return mdl.u[i] - mdl.u[j] + 7 * mdl.x[i, j] <= 6

    model.subtour = pyo.Constraint(model.B, rule=subtour_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.travel_cost[i, j] * model.x[i, j]
            for i, j in model.A
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}