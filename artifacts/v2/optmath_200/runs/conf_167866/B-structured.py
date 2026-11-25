# IR: {"sets":{"O":"0..7","D":"0..8"},"params":{"supply":"params['supply'][o]","demand":"params['demand'][d]","cost":"params['cost'][o,d]","capacity":"params['capacity'][o,d]; missing or None means +infinity"},"variables":{"shipment[o,d]":"nonnegative continuous"},"constraints":["sum_d shipment[o,d] = supply[o] for every o","sum_o shipment[o,d] = demand[d] for every d","shipment[o,d] <= capacity[o,d] for every finite capacity"],"objective":"minimize sum_o sum_d cost[o,d]*shipment[o,d]"}
from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


_MISSING = object()


def _entry(data, *indices, default=_MISSING):
    """Accept sequences, nested integer-key mappings, or tuple-key mappings."""
    try:
        if len(indices) == 2 and isinstance(data, Mapping):
            if indices in data:
                return data[indices]

        value = data
        for position in indices:
            value = value[position]
        return value
    except (KeyError, IndexError):
        if default is _MISSING:
            raise
        return default


def solve(params):
    supply_data = params["supply"]
    demand_data = params["demand"]
    cost_data = params["cost"]
    raw_capacity_data = params["capacity"]

    model = pyo.ConcreteModel()
    model.origins = pyo.RangeSet(0, 7)
    model.destinations = pyo.RangeSet(0, 8)

    capacity_data = {}
    for origin in model.origins:
        for destination in model.destinations:
            capacity_value = _entry(
                raw_capacity_data, origin, destination, default=None
            )
            capacity_data[origin, destination] = (
                float("inf") if capacity_value is None else capacity_value
            )

    model.origin_supply = pyo.Param(
        model.origins,
        initialize={
            origin: _entry(supply_data, origin)
            for origin in model.origins
        },
        within=pyo.NonNegativeReals,
    )
    model.destination_demand = pyo.Param(
        model.destinations,
        initialize={
            destination: _entry(demand_data, destination)
            for destination in model.destinations
        },
        within=pyo.NonNegativeReals,
    )
    model.unit_cost = pyo.Param(
        model.origins,
        model.destinations,
        initialize={
            (origin, destination): _entry(cost_data, origin, destination)
            for origin in model.origins
            for destination in model.destinations
        },
        within=pyo.Reals,
    )
    model.arc_capacity = pyo.Param(
        model.origins,
        model.destinations,
        initialize=capacity_data,
        within=pyo.NonNegativeReals,
    )

    model.shipment = pyo.Var(
        model.origins,
        model.destinations,
        domain=pyo.NonNegativeReals,
    )

    def supply_rule(instance, origin):
        return (
            sum(
                instance.shipment[origin, destination]
                for destination in instance.destinations
            )
            == instance.origin_supply[origin]
        )

    def demand_rule(instance, destination):
        return (
            sum(
                instance.shipment[origin, destination]
                for origin in instance.origins
            )
            == instance.destination_demand[destination]
        )

    def capacity_rule(instance, origin, destination):
        if capacity_data[origin, destination] == float("inf"):
            return pyo.Constraint.Skip
        return (
            instance.shipment[origin, destination]
            <= instance.arc_capacity[origin, destination]
        )

    model.supply_balance = pyo.Constraint(model.origins, rule=supply_rule)
    model.demand_balance = pyo.Constraint(model.destinations, rule=demand_rule)
    model.capacity_limit = pyo.Constraint(
        model.origins,
        model.destinations,
        rule=capacity_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.unit_cost[origin, destination]
            * model.shipment[origin, destination]
            for origin in model.origins
            for destination in model.destinations
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        # APPsi raises this when its default solution loader has no solution.
        # Unexpected solver errors remain visible to the caller.
        if "a feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}