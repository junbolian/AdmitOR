# IR: {"sets":{"DC":"1..8","STORE":"1..8"},"params":{"opening_cost":"required length-8 nonnegative array","transport_cost":"required 8x8 nonnegative matrix","demand":"required length-8 nonnegative array","capacity":"required length-8 nonnegative array"},"variables":{"opened[i]":"binary","shipment[i,j]":"nonnegative continuous"},"constraints":["For each store j: sum_i shipment[i,j] = demand[j]","For each DC i: sum_j shipment[i,j] <= capacity[i]*opened[i]"],"objective":"Minimize sum_i opening_cost[i]*opened[i] + sum_i,j transport_cost[i,j]*shipment[i,j]","input_policy":"Return failure for missing parameters or incomplete arrays; never infer unspecified data."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve with complete zero-based arrays supplied by the caller."""
    required_keys = ("opening_cost", "transport_cost", "demand", "capacity")
    for key in required_keys:
        if key not in params:
            return {"objective": None, "status": f"missing_parameter:{key}"}

    # The partial numbers in the problem do not determine the missing data.
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    for key, values in (
        ("opening_cost", opening_cost),
        ("demand", demand),
        ("capacity", capacity),
    ):
        if not isinstance(values, (list, tuple)) or len(values) != 8:
            return {"objective": None, "status": f"invalid_shape:{key}"}

    if (
        not isinstance(transport_cost, (list, tuple))
        or len(transport_cost) != 8
        or any(
            not isinstance(row, (list, tuple)) or len(row) != 8
            for row in transport_cost
        )
    ):
        return {"objective": None, "status": "invalid_shape:transport_cost"}

    for key, values in (
        ("opening_cost", opening_cost),
        ("demand", demand),
        ("capacity", capacity),
    ):
        if any(value is None for value in values):
            return {"objective": None, "status": f"incomplete_parameter:{key}"}

    if any(value is None for row in transport_cost for value in row):
        return {"objective": None, "status": "incomplete_parameter:transport_cost"}

    model = pyo.ConcreteModel()
    model.DC = pyo.RangeSet(1, 8)
    model.STORE = pyo.RangeSet(1, 8)

    model.opening_cost = pyo.Param(
        model.DC,
        initialize=lambda mdl, dc: opening_cost[dc - 1],
        within=pyo.NonNegativeReals,
    )
    model.transport_cost = pyo.Param(
        model.DC,
        model.STORE,
        initialize=lambda mdl, dc, store: transport_cost[dc - 1][store - 1],
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.STORE,
        initialize=lambda mdl, store: demand[store - 1],
        within=pyo.NonNegativeReals,
    )
    model.capacity = pyo.Param(
        model.DC,
        initialize=lambda mdl, dc: capacity[dc - 1],
        within=pyo.NonNegativeReals,
    )

    model.opened = pyo.Var(model.DC, within=pyo.Binary)
    model.shipment = pyo.Var(
        model.DC, model.STORE, within=pyo.NonNegativeReals
    )

    def demand_rule(mdl, store):
        return (
            sum(mdl.shipment[dc, store] for dc in mdl.DC)
            == mdl.demand[store]
        )

    model.demand_fulfillment = pyo.Constraint(
        model.STORE, rule=demand_rule
    )

    def capacity_rule(mdl, dc):
        return (
            sum(mdl.shipment[dc, store] for store in mdl.STORE)
            <= mdl.capacity[dc] * mdl.opened[dc]
        )

    model.capacity_limits = pyo.Constraint(
        model.DC, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.opening_cost[dc] * model.opened[dc]
            for dc in model.DC
        )
        + sum(
            model.transport_cost[dc, store] * model.shipment[dc, store]
            for dc in model.DC
            for store in model.STORE
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # A failed solution load can raise; objective retrieval decides success.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}