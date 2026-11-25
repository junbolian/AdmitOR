# IR: {"sets":{"V":[0,1,2,3,4],"N":[1,2,3,4],"A":"{(i,j) in V x V: i != j}"},"params":{"cost[i,j]":"params[f'cost_{i}_{j}'] for (i,j) in A"},"variables":{"x[i,j]":{"type":"binary","index":"A"},"u[i]":{"type":"integer","index":"V","bounds":"[0,0] if i=0, otherwise [1,4]"}},"constraints":["For each i in V: sum(x[i,j] for j in V if j != i) = 1","For each j in V: sum(x[i,j] for i in V if i != j) = 1","For each distinct i,j in N: u[i] - u[j] + 5*x[i,j] <= 4"],"objective":{"sense":"minimize","expression":"sum(cost[i,j]*x[i,j] for (i,j) in A)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.V = pyo.Set(initialize=range(5), ordered=True)
    model.N = pyo.Set(initialize=range(1, 5), ordered=True)
    model.A = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(5)
            for j in range(5)
            if i != j
        ],
    )

    model.cost = pyo.Param(
        model.A,
        initialize={
            (i, j): params[f"cost_{i}_{j}"]
            for i, j in model.A
        },
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.A, domain=pyo.Binary)

    def position_bounds(model, i):
        return (0, 0) if i == 0 else (1, 4)

    model.u = pyo.Var(
        model.V,
        domain=pyo.Integers,
        bounds=position_bounds,
    )

    def departure_rule(model, i):
        return sum(model.x[i, j] for j in model.V if j != i) == 1

    model.departure = pyo.Constraint(model.V, rule=departure_rule)

    def arrival_rule(model, j):
        return sum(model.x[i, j] for i in model.V if i != j) == 1

    model.arrival = pyo.Constraint(model.V, rule=arrival_rule)

    def subtour_rule(model, i, j):
        if i == j:
            return pyo.Constraint.Skip
        return model.u[i] - model.u[j] + 5 * model.x[i, j] <= 4

    model.subtour = pyo.Constraint(model.N, model.N, rule=subtour_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[i, j] * model.x[i, j]
            for i, j in model.A
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}