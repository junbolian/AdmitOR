# IR: {"sets":{"O":"0..9","D":"0..7"},"params":{"supply":"params['supply'][i]","demand":"params['demand'][j]","cost":"params['cost'][i][j] or params['cost'][i,j]","capacity":"params['capacity'][i][j] or params['capacity'][i,j]"},"variables":{"shipment[i,j]":"continuous, nonnegative"},"constraints":["sum(shipment[i,j] for j in D) <= supply[i] for i in O","sum(shipment[i,j] for i in O) == demand[j] for j in D","shipment[i,j] <= capacity[i,j] for (i,j) in O x D"],"objective":"minimize sum(cost[i,j]*shipment[i,j] for (i,j) in O x D)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _pair_value(values, origin, destination):
    """Accept nested arrays/mappings or mappings keyed by (origin, destination)."""
    if isinstance(values, Mapping) and (origin, destination) in values:
        return values[origin, destination]
    return values[origin][destination]


def solve(params):
    supply_data = params["supply"]
    demand_data = params["demand"]
    cost_data = params["cost"]
    capacity_data = params["capacity"]

    model = pyo.ConcreteModel()
    model.origins = pyo.RangeSet(0, 9)
    model.destinations = pyo.RangeSet(0, 7)

    model.supply = pyo.Param(
        model.origins,
        initialize=lambda mdl, origin: supply_data[origin],
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.destinations,
        initialize=lambda mdl, destination: demand_data[destination],
        within=pyo.NonNegativeReals,
    )
    model.transport_cost = pyo.Param(
        model.origins,
        model.destinations,
        initialize=lambda mdl, origin, destination: _pair_value(
            cost_data, origin, destination
        ),
        within=pyo.Reals,
    )
    model.route_capacity = pyo.Param(
        model.origins,
        model.destinations,
        initialize=lambda mdl, origin, destination: _pair_value(
            capacity_data, origin, destination
        ),
        within=pyo.NonNegativeReals,
    )

    model.shipment = pyo.Var(
        model.origins,
        model.destinations,
        domain=pyo.NonNegativeReals,
    )

    def supply_rule(mdl, origin):
        return (
            sum(mdl.shipment[origin, destination] for destination in mdl.destinations)
            <= mdl.supply[origin]
        )

    def demand_rule(mdl, destination):
        return (
            sum(mdl.shipment[origin, destination] for origin in mdl.origins)
            == mdl.demand[destination]
        )

    def capacity_rule(mdl, origin, destination):
        return (
            mdl.shipment[origin, destination]
            <= mdl.route_capacity[origin, destination]
        )

    model.supply_limits = pyo.Constraint(model.origins, rule=supply_rule)
    model.demand_requirements = pyo.Constraint(
        model.destinations, rule=demand_rule
    )
    model.capacity_limits = pyo.Constraint(
        model.origins, model.destinations, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.transport_cost[origin, destination]
            * model.shipment[origin, destination]
            for origin in model.origins
            for destination in model.destinations
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