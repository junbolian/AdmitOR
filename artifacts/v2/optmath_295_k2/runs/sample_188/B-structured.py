# IR: {"sets":{"origins":"0..7","destinations":"0..7"},"params":{"supply":"origins -> nonnegative real","demand":"destinations -> nonnegative real","transport_cost":"origins x destinations -> real","pair_capacity":"origins x destinations -> nonnegative real"},"variables":{"shipment[i,j]":"nonnegative continuous"},"constraints":["sum(j, shipment[i,j]) == supply[i] for each origin i","sum(i, shipment[i,j]) == demand[j] for each destination j","shipment[i,j] <= pair_capacity[i,j] for each pair (i,j)"],"objective":"minimize sum(i,j, transport_cost[i,j] * shipment[i,j])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    transport_cost = params["transport_cost"]
    pair_capacity = params["pair_capacity"]

    model = pyo.ConcreteModel()

    model.origins = pyo.RangeSet(0, 7)
    model.destinations = pyo.RangeSet(0, 7)

    model.supply = pyo.Param(
        model.origins,
        initialize={i: supply[i] for i in model.origins},
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.destinations,
        initialize={j: demand[j] for j in model.destinations},
        within=pyo.NonNegativeReals,
    )
    model.transport_cost = pyo.Param(
        model.origins,
        model.destinations,
        initialize={
            (i, j): transport_cost[i][j]
            for i in model.origins
            for j in model.destinations
        },
        within=pyo.Reals,
    )
    model.pair_capacity = pyo.Param(
        model.origins,
        model.destinations,
        initialize={
            (i, j): pair_capacity[i][j]
            for i in model.origins
            for j in model.destinations
        },
        within=pyo.NonNegativeReals,
    )

    model.shipment = pyo.Var(
        model.origins,
        model.destinations,
        domain=pyo.NonNegativeReals,
    )

    model.supply_balance = pyo.Constraint(
        model.origins,
        rule=lambda mdl, i: sum(
            mdl.shipment[i, j] for j in mdl.destinations
        ) == mdl.supply[i],
    )
    model.demand_balance = pyo.Constraint(
        model.destinations,
        rule=lambda mdl, j: sum(
            mdl.shipment[i, j] for i in mdl.origins
        ) == mdl.demand[j],
    )
    model.capacity_limit = pyo.Constraint(
        model.origins,
        model.destinations,
        rule=lambda mdl, i, j: (
            mdl.shipment[i, j] <= mdl.pair_capacity[i, j]
        ),
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.transport_cost[i, j] * model.shipment[i, j]
            for i in model.origins
            for j in model.destinations
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