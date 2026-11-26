# IR: {"sets":{"centers":"0..8","stores":"0..6"},"params":{"opening_costs":"params['opening_costs']: 9 finite numbers","transport_costs":"params['transport_costs']: 9x7 finite numbers; missing entries are unknown, not zero","demands":"params['demands']: 7 finite nonnegative numbers","capacities":"params['capacities']: 9 finite nonnegative numbers"},"variables":{"opened[i]":"Binary","shipment[i,j]":"NonNegativeReals"},"constraints":["For each store j: sum_i shipment[i,j] == demands[j].","For each center i: sum_j shipment[i,j] <= capacities[i]*opened[i]."],"objective":"Minimize sum_i opening_costs[i]*opened[i] + sum_i,j transport_costs[i][j]*shipment[i,j].","validation":["Reject invalid dimensions, nonnumeric values, and nonfinite values.","Return insufficient_transport_data if transportation costs are omitted or null; never invent costs."],"solution":"Call Highs().solve(model); determine success solely by retrieving float(pyo.value(model.total_cost)); do not inspect termination conditions."}

import math

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """
    Solve the capacitated facility-location problem with divisible shipments.

    Inputs are zero-based sequences in center/store order.

    The supplied problem statement omits transportation costs. No script can
    determine its numerical optimum without those inputs or an additional
    explicit assumption. This implementation accepts a complete cost matrix
    and returns insufficient_transport_data when entries remain unknown.
    """
    opening_costs = params["opening_costs"]
    transport_costs = params["transport_costs"]
    demands = params["demands"]
    capacities = params["capacities"]

    center_count = 9
    store_count = 7

    if any(
        values is None
        for values in (opening_costs, demands, capacities)
    ):
        return {"objective": None, "status": "missing_parameter_value"}

    if (
        len(opening_costs) != center_count
        or len(demands) != store_count
        or len(capacities) != center_count
    ):
        return {"objective": None, "status": "invalid_dimensions"}

    if transport_costs is None:
        return {"objective": None, "status": "insufficient_transport_data"}

    if len(transport_costs) < center_count:
        return {"objective": None, "status": "insufficient_transport_data"}

    if len(transport_costs) > center_count:
        return {"objective": None, "status": "invalid_dimensions"}

    for row in transport_costs:
        if row is None or len(row) < store_count:
            return {"objective": None, "status": "insufficient_transport_data"}
        if len(row) > store_count:
            return {"objective": None, "status": "invalid_dimensions"}
        if any(value is None for value in row):
            return {"objective": None, "status": "insufficient_transport_data"}

    if any(
        value is None
        for values in (opening_costs, demands, capacities)
        for value in values
    ):
        return {"objective": None, "status": "missing_parameter_value"}

    try:
        fixed_cost = [float(value) for value in opening_costs]
        demand = [float(value) for value in demands]
        capacity = [float(value) for value in capacities]
        shipping_cost = [
            [float(value) for value in row]
            for row in transport_costs
        ]
    except (TypeError, ValueError, OverflowError):
        return {"objective": None, "status": "invalid_numeric_input"}

    if not all(
        math.isfinite(value)
        for values in (fixed_cost, demand, capacity, *shipping_cost)
        for value in values
    ):
        return {"objective": None, "status": "nonfinite_parameter"}

    if any(value < 0 for value in demand + capacity):
        return {"objective": None, "status": "negative_demand_or_capacity"}

    model = pyo.ConcreteModel()

    model.centers = pyo.RangeSet(0, center_count - 1)
    model.stores = pyo.RangeSet(0, store_count - 1)

    model.fixed_cost = pyo.Param(
        model.centers,
        initialize={i: fixed_cost[i] for i in range(center_count)},
        within=pyo.Reals,
    )
    model.shipping_cost = pyo.Param(
        model.centers,
        model.stores,
        initialize={
            (i, j): shipping_cost[i][j]
            for i in range(center_count)
            for j in range(store_count)
        },
        within=pyo.Reals,
    )
    model.store_demand = pyo.Param(
        model.stores,
        initialize={j: demand[j] for j in range(store_count)},
        within=pyo.NonNegativeReals,
    )
    model.center_capacity = pyo.Param(
        model.centers,
        initialize={i: capacity[i] for i in range(center_count)},
        within=pyo.NonNegativeReals,
    )

    model.opened = pyo.Var(model.centers, domain=pyo.Binary)
    model.shipment = pyo.Var(
        model.centers, model.stores, domain=pyo.NonNegativeReals
    )

    def demand_rule(instance, j):
        return (
            sum(instance.shipment[i, j] for i in instance.centers)
            == instance.store_demand[j]
        )

    def capacity_rule(instance, i):
        return (
            sum(instance.shipment[i, j] for j in instance.stores)
            <= instance.center_capacity[i] * instance.opened[i]
        )

    model.demand_fulfillment = pyo.Constraint(
        model.stores, rule=demand_rule
    )
    model.capacity_limits = pyo.Constraint(
        model.centers, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.fixed_cost[i] * model.opened[i]
                for i in model.centers
            )
            + sum(
                model.shipping_cost[i, j] * model.shipment[i, j]
                for i in model.centers
                for j in model.stores
            )
        ),
        sense=pyo.minimize,
    )

    failure_reason = "objective_unavailable"
    try:
        Highs().solve(model)
    except RuntimeError:
        # APPSI can raise when a feasible solution cannot be loaded.
        # Still determine success only through objective retrieval.
        failure_reason = "infeasible_or_failed"

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": failure_reason}

    return {"objective": obj_val, "status": "optimal"}