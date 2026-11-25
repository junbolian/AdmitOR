# IR: {"sets":{"I":"0..5","J":"0..7"},"params":{"supply":"params['supply'][i]","demand":"params['demand'][j]","cost":"params['cost'][i][j] or params['cost'][i,j]","capacity":"params['capacity'][i][j] or params['capacity'][i,j]"},"variables":{"shipment[i,j]":"nonnegative continuous"},"constraints":["sum(j in J, shipment[i,j]) == supply[i] for i in I","sum(i in I, shipment[i,j]) == demand[j] for j in J","shipment[i,j] <= capacity[i,j] for (i,j) in I x J"],"objective":"minimize sum((i,j) in I x J, cost[i,j] * shipment[i,j])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _route_value(data, i, j):
    """Support nested arrays/mappings and mappings keyed by (i, j)."""
    if isinstance(data, dict) and (i, j) in data:
        return data[i, j]
    return data[i][j]


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()
    model.origins = pyo.RangeSet(0, 5)
    model.destinations = pyo.RangeSet(0, 7)

    model.supply_data = pyo.Param(
        model.origins,
        initialize=lambda mdl, i: supply[i],
        within=pyo.NonNegativeReals,
    )
    model.demand_data = pyo.Param(
        model.destinations,
        initialize=lambda mdl, j: demand[j],
        within=pyo.NonNegativeReals,
    )
    model.cost_data = pyo.Param(
        model.origins,
        model.destinations,
        initialize=lambda mdl, i, j: _route_value(cost, i, j),
        within=pyo.Reals,
    )
    model.capacity_data = pyo.Param(
        model.origins,
        model.destinations,
        initialize=lambda mdl, i, j: _route_value(capacity, i, j),
        within=pyo.NonNegativeReals,
    )

    model.shipment = pyo.Var(
        model.origins,
        model.destinations,
        domain=pyo.NonNegativeReals,
    )

    def supply_rule(mdl, i):
        return (
            sum(mdl.shipment[i, j] for j in mdl.destinations)
            == mdl.supply_data[i]
        )

    def demand_rule(mdl, j):
        return (
            sum(mdl.shipment[i, j] for i in mdl.origins)
            == mdl.demand_data[j]
        )

    def capacity_rule(mdl, i, j):
        return mdl.shipment[i, j] <= mdl.capacity_data[i, j]

    model.supply_balance = pyo.Constraint(model.origins, rule=supply_rule)
    model.demand_balance = pyo.Constraint(model.destinations, rule=demand_rule)
    model.route_limits = pyo.Constraint(
        model.origins,
        model.destinations,
        rule=capacity_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost_data[i, j] * model.shipment[i, j]
            for i in model.origins
            for j in model.destinations
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}