# {
#   "sets": {"origins": "0..9", "destinations": "0..7"},
#   "params": {"supply": "params['supply'][i], nonnegative", "demand": "params['demand'][j], nonnegative", "cost": "params['cost'][i][j] or params['cost'][i,j], real", "capacity": "params['capacity'][i][j] or params['capacity'][i,j], nonnegative"},
#   "variables": {"shipment[i,j]": "continuous, nonnegative"},
#   "constraints": [
#     "For each origin i: sum_j shipment[i,j] <= supply[i]",
#     "For each destination j: sum_i shipment[i,j] == demand[j]",
#     "For each origin-destination pair (i,j): shipment[i,j] <= capacity[i,j]"
#   ],
#   "objective": "minimize sum_i sum_j cost[i,j] * shipment[i,j]"
# }

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _pair_value(data, origin, destination):
    """Accept a nested sequence/mapping or a mapping keyed by (i, j)."""
    if isinstance(data, Mapping) and (origin, destination) in data:
        return data[origin, destination]
    return data[origin][destination]


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
    model.cost = pyo.Param(
        model.origins,
        model.destinations,
        initialize=lambda mdl, origin, destination: _pair_value(
            cost_data, origin, destination
        ),
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
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
            sum(
                mdl.shipment[origin, destination]
                for destination in mdl.destinations
            )
            <= mdl.supply[origin]
        )

    def demand_rule(mdl, destination):
        return (
            sum(
                mdl.shipment[origin, destination]
                for origin in mdl.origins
            )
            == mdl.demand[destination]
        )

    def capacity_rule(mdl, origin, destination):
        return (
            mdl.shipment[origin, destination]
            <= mdl.capacity[origin, destination]
        )

    model.supply_limits = pyo.Constraint(
        model.origins, rule=supply_rule
    )
    model.demand_requirements = pyo.Constraint(
        model.destinations, rule=demand_rule
    )
    model.route_limits = pyo.Constraint(
        model.origins, model.destinations, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[origin, destination]
            * model.shipment[origin, destination]
            for origin in model.origins
            for destination in model.destinations
        ),
        sense=pyo.minimize,
    )

    # APPSI can raise RuntimeError when no feasible solution can be loaded.
    # Objective retrieval alone determines whether this call succeeds.
    failure_reason = "objective_unavailable"
    try:
        Highs().solve(model)
    except RuntimeError:
        failure_reason = "solve_failed"

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": failure_reason}

    return {"objective": obj_val, "status": "optimal"}