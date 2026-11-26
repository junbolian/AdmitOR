# IR: {"sets":{"centers":"1..7","stores":"1..7"},"params":{"opening_cost":"real[centers]","transport_cost":"real[centers,stores]","demand":"nonnegative_real[stores]","capacity":"nonnegative_real[centers]"},"variables":{"opened":"binary[centers]","shipment":"nonnegative_real[centers,stores]"},"constraints":["For each store j: sum_i shipment[i,j] = demand[j]","For each center i: sum_j shipment[i,j] <= capacity[i] * opened[i]"],"objective":"Minimize sum_i opening_cost[i]*opened[i] + sum_i,j transport_cost[i,j]*shipment[i,j]"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Accept arrays in center/store order or mappings keyed by 1..7."""

    def entry(values, position):
        if isinstance(values, Mapping):
            return values[position]
        return values[position - 1]

    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()
    model.centers = pyo.RangeSet(1, 7)
    model.stores = pyo.RangeSet(1, 7)

    model.opening_cost = pyo.Param(
        model.centers,
        initialize={
            center: entry(opening_cost, center)
            for center in model.centers
        },
        within=pyo.Reals,
    )
    model.transport_cost = pyo.Param(
        model.centers,
        model.stores,
        initialize={
            (center, store): entry(entry(transport_cost, center), store)
            for center in model.centers
            for store in model.stores
        },
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        model.stores,
        initialize={
            store: entry(demand, store)
            for store in model.stores
        },
        within=pyo.NonNegativeReals,
    )
    model.capacity = pyo.Param(
        model.centers,
        initialize={
            center: entry(capacity, center)
            for center in model.centers
        },
        within=pyo.NonNegativeReals,
    )

    model.opened = pyo.Var(model.centers, domain=pyo.Binary)
    model.shipment = pyo.Var(
        model.centers,
        model.stores,
        domain=pyo.NonNegativeReals,
    )

    def demand_rule(instance, store):
        return (
            sum(
                instance.shipment[center, store]
                for center in instance.centers
            )
            == instance.demand[store]
        )

    model.demand_balance = pyo.Constraint(
        model.stores,
        rule=demand_rule,
    )

    def capacity_rule(instance, center):
        return (
            sum(
                instance.shipment[center, store]
                for store in instance.stores
            )
            <= instance.capacity[center] * instance.opened[center]
        )

    model.capacity_limit = pyo.Constraint(
        model.centers,
        rule=capacity_rule,
    )

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.opening_cost[center] * model.opened[center]
                for center in model.centers
            )
            + sum(
                model.transport_cost[center, store]
                * model.shipment[center, store]
                for center in model.centers
                for store in model.stores
            )
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "no_objective"}

    return {"objective": obj_val, "status": "optimal"}