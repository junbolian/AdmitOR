# IR: {"sets":{"I":"0..6","J":"0..6"},"params":{"supply":"supply[i] >= 0","demand":"demand[j] >= 0","cost":"cost[i,j] real","capacity":"capacity[i,j] >= 0"},"variables":{"shipment[i,j]":"continuous nonnegative"},"constraints":["sum_j shipment[i,j] = supply[i] for each i","sum_i shipment[i,j] = demand[j] for each j","shipment[i,j] <= capacity[i,j] for each i,j"],"objective":"minimize sum_i sum_j cost[i,j] * shipment[i,j]"}
from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Accept vectors and either nested matrices or (i, j)-keyed mappings."""
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    def matrix_value(data, i, j):
        if isinstance(data, Mapping) and (i, j) in data:
            return data[i, j]
        return data[i][j]

    model = pyo.ConcreteModel()
    model.origins = pyo.RangeSet(0, 6)
    model.destinations = pyo.RangeSet(0, 6)

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
        initialize=lambda mdl, i, j: matrix_value(cost, i, j),
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.origins,
        model.destinations,
        initialize=lambda mdl, i, j: matrix_value(capacity, i, j),
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
    model.route_capacity = pyo.Constraint(
        model.origins,
        model.destinations,
        rule=lambda mdl, i, j: mdl.shipment[i, j] <= mdl.capacity[i, j],
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
        # APPSI raises this when it cannot load a feasible solution.
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "infeasible_or_failed"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}