# IR: {"sets":{"I":"0..4","J":"0..6"},"params":{"supply":"nonnegative[I], from params['supply']","demand":"nonnegative[J], from params['demand']","cost":"real[I,J], from params['cost']","limit":"nonnegative[I,J], from params['limit']"},"variables":{"shipment[I,J]":"continuous, nonnegative"},"constraints":["sum(shipment[i,j] for j in J) <= supply[i] for i in I","sum(shipment[i,j] for i in I) == demand[j] for j in J","shipment[i,j] <= limit[i,j] for (i,j) in I x J"],"objective":"minimize sum(cost[i,j] * shipment[i,j] for (i,j) in I x J)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve the transportation LP using supplied vectors and nested matrices."""
    supply = params["supply"]
    demand = params["demand"]
    cost = params["cost"]
    limit = params["limit"]

    model = pyo.ConcreteModel()

    model.origins = pyo.RangeSet(0, 4)
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
        initialize=lambda mdl, i, j: cost[i][j],
        within=pyo.Reals,
    )
    model.route_limit = pyo.Param(
        model.origins,
        model.destinations,
        initialize=lambda mdl, i, j: limit[i][j],
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
            <= mdl.supply[i]
        )

    model.supply_constraints = pyo.Constraint(
        model.origins, rule=supply_rule
    )

    def demand_rule(mdl, j):
        return (
            sum(mdl.shipment[i, j] for i in mdl.origins)
            == mdl.demand[j]
        )

    model.demand_constraints = pyo.Constraint(
        model.destinations, rule=demand_rule
    )

    def route_limit_rule(mdl, i, j):
        return mdl.shipment[i, j] <= mdl.route_limit[i, j]

    model.route_constraints = pyo.Constraint(
        model.origins,
        model.destinations,
        rule=route_limit_rule,
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
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}