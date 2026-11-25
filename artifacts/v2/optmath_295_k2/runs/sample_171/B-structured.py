# IR: {"sets":{"I":"0..5","J":"0..7"},"params":{"supply":"nonnegative real[I], from params['supply']","demand":"nonnegative real[J], from params['demand']","cost":"real[I,J], from params['cost']","capacity":"nonnegative real[I,J], from params['capacity']"},"variables":{"shipment[i,j]":"continuous nonnegative real, i in I, j in J"},"constraints":["sum(shipment[i,j] for j in J) == supply[i], for each i in I","sum(shipment[i,j] for i in I) == demand[j], for each j in J","shipment[i,j] <= capacity[i,j], for each (i,j) in I x J"],"objective":"minimize sum(cost[i,j] * shipment[i,j] for i in I, j in J)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()
    model.origins = pyo.RangeSet(0, 5)
    model.destinations = pyo.RangeSet(0, 7)

    model.supply = pyo.Param(
        model.origins,
        initialize=lambda mdl, i: supply[i],
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.destinations,
        initialize=lambda mdl, j: demand[j],
        within=pyo.NonNegativeReals,
    )
    model.cost = pyo.Param(
        model.origins,
        model.destinations,
        initialize=lambda mdl, i, j: cost[i][j],
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.origins,
        model.destinations,
        initialize=lambda mdl, i, j: capacity[i][j],
        within=pyo.NonNegativeReals,
    )

    model.shipment = pyo.Var(
        model.origins,
        model.destinations,
        domain=pyo.NonNegativeReals,
    )

    model.supply_balance = pyo.Constraint(
        model.origins,
        rule=lambda mdl, i: (
            sum(mdl.shipment[i, j] for j in mdl.destinations)
            == mdl.supply[i]
        ),
    )
    model.demand_balance = pyo.Constraint(
        model.destinations,
        rule=lambda mdl, j: (
            sum(mdl.shipment[i, j] for i in mdl.origins)
            == mdl.demand[j]
        ),
    )
    model.route_capacity = pyo.Constraint(
        model.origins,
        model.destinations,
        rule=lambda mdl, i, j: (
            mdl.shipment[i, j] <= mdl.capacity[i, j]
        ),
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[i, j] * model.shipment[i, j]
            for i in model.origins
            for j in model.destinations
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        # Leave success determination to objective retrieval below.
        if "a feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}