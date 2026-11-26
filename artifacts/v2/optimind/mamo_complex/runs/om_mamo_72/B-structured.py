# IR: {"sets":{"V":[1,2,3,4,5,6],"A":"{(i,j) in V x V: i != j}","U":[2,3,4,5,6]},"params":{"cost[i,j]":"params[f'cost_{i}_{j}'] for (i,j) in A"},"variables":{"x[i,j]":"binary for (i,j) in A","u[i]":"continuous in [1,5] for i in U"},"constraints":["sum(x[i,j] for j in V if j != i) = 1 for i in V","sum(x[i,j] for i in V if i != j) = 1 for j in V","u[i] - u[j] + 5*x[i,j] <= 4 for i,j in U with i != j"],"objective":"minimize sum(cost[i,j]*x[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.cities = pyo.RangeSet(1, 6)
    model.nonroot_cities = pyo.RangeSet(2, 6)
    model.arcs = pyo.Set(
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
    model.u = pyo.Var(
        model.nonroot_cities,
        domain=pyo.Reals,
        bounds=(1, 5),
    )

    def outgoing_rule(model, i):
        return sum(
            model.x[i, j] for j in model.cities if j != i
        ) == 1

    model.outgoing = pyo.Constraint(model.cities, rule=outgoing_rule)

    def incoming_rule(model, j):
        return sum(
            model.x[i, j] for i in model.cities if i != j
        ) == 1

    model.incoming = pyo.Constraint(model.cities, rule=incoming_rule)

    def subtour_rule(model, i, j):
        if i == j:
            return pyo.Constraint.Skip
        return model.u[i] - model.u[j] + 5 * model.x[i, j] <= 4

    model.subtour_elimination = pyo.Constraint(
        model.nonroot_cities,
        model.nonroot_cities,
        rule=subtour_rule,
    )

    model.tour_cost = pyo.Objective(
        expr=sum(
            model.travel_cost[i, j] * model.x[i, j]
            for i, j in model.arcs
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.tour_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}