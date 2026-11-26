# IR: {"sets":{"R":"0..5","A":"{(i,j) in R x R: i != j}"},"params":{"supply":"params['supply'][i] for i in R","demand":"params['demand'][i] for i in R","cost":"params['cost'][i][j] for (i,j) in A"},"variables":{"flow[i,j]":"nonnegative continuous for (i,j) in A"},"constraints":["supply[i] + sum(flow[j,i] for j != i) - sum(flow[i,j] for j != i) >= demand[i] for i in R"],"objective":"minimize sum(cost[i,j] * flow[i,j] for (i,j) in A)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.regions = pyo.RangeSet(0, 5)
    model.routes = pyo.Set(
        dimen=2,
        initialize=[
            (i, j)
            for i in range(6)
            for j in range(6)
            if i != j
        ],
    )

    model.initial_supply = pyo.Param(
        model.regions,
        initialize={i: params["supply"][i] for i in range(6)},
    )
    model.required_food = pyo.Param(
        model.regions,
        initialize={i: params["demand"][i] for i in range(6)},
    )
    model.transport_cost = pyo.Param(
        model.routes,
        initialize={
            (i, j): params["cost"][i][j]
            for i in range(6)
            for j in range(6)
            if i != j
        },
    )

    model.flow = pyo.Var(model.routes, domain=pyo.NonNegativeReals)

    def food_balance_rule(instance, i):
        incoming = sum(
            instance.flow[j, i]
            for j in instance.regions
            if j != i
        )
        outgoing = sum(
            instance.flow[i, j]
            for j in instance.regions
            if j != i
        )
        return (
            instance.initial_supply[i] + incoming - outgoing
            >= instance.required_food[i]
        )

    model.food_balance = pyo.Constraint(
        model.regions,
        rule=food_balance_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.transport_cost[i, j] * model.flow[i, j]
            for i, j in model.routes
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}