# IR: {"sets":{"V":[0,1,2,3,4,5,6],"A":"{(i,j) in V x V: i != j}","B":"{(i,j) in A: i != 0 and j != 0}"},"params":{"cost[i,j]":"params['cost_{i}_{j}'] for every (i,j) in A"},"variables":{"x[i,j]":"Binary, (i,j) in A","u[i]":"Integer in [0,6], i in V"},"constraints":["sum(x[i,j] for j != i) = 1 for each i in V","sum(x[i,j] for i != j) = 1 for each j in V","u[0] = 0","u[i] - u[j] + 7*x[i,j] <= 6 for each (i,j) in B"],"objective":"minimize sum(cost[i,j]*x[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.cities = pyo.Set(initialize=range(7), ordered=True)
    model.arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(7)
            for j in range(7)
            if i != j
        ],
    )
    model.non_depot_arcs = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(1, 7)
            for j in range(1, 7)
            if i != j
        ],
    )

    model.travel_cost = pyo.Param(
        model.arcs,
        initialize={
            (i, j): params[f"cost_{i}_{j}"]
            for i, j in model.arcs
        },
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)
    model.u = pyo.Var(model.cities, domain=pyo.Integers, bounds=(0, 6))

    def departure_rule(instance, i):
        return sum(
            instance.x[i, j] for j in instance.cities if j != i
        ) == 1

    model.departure_once = pyo.Constraint(
        model.cities, rule=departure_rule
    )

    def arrival_rule(instance, j):
        return sum(
            instance.x[i, j] for i in instance.cities if i != j
        ) == 1

    model.arrival_once = pyo.Constraint(
        model.cities, rule=arrival_rule
    )

    model.depot_position = pyo.Constraint(expr=model.u[0] == 0)

    def subtour_rule(instance, i, j):
        return instance.u[i] - instance.u[j] + 7 * instance.x[i, j] <= 6

    model.subtour_elimination = pyo.Constraint(
        model.non_depot_arcs, rule=subtour_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.travel_cost[i, j] * model.x[i, j]
            for i, j in model.arcs
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