# IR: {"sets":{"origins":"0..6","destinations":"0..6"},"params":{"supply":"params['supply'][i]","demand":"params['demand'][j]","cost":"params['cost'][i][j]"},"variables":{"shipment[i,j]":"NonNegativeReals"},"constraints":["sum(shipment[i,j] for j in destinations) == supply[i] for each origin i","sum(shipment[i,j] for i in origins) == demand[j] for each destination j"],"objective":"minimize sum(cost[i,j] * shipment[i,j] for i in origins for j in destinations)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.origins = pyo.RangeSet(0, 6)
    model.destinations = pyo.RangeSet(0, 6)

    model.supply = pyo.Param(
        model.origins,
        initialize=lambda model, i: params["supply"][i],
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        model.destinations,
        initialize=lambda model, j: params["demand"][j],
        within=pyo.Reals,
    )
    model.cost = pyo.Param(
        model.origins,
        model.destinations,
        initialize=lambda model, i, j: params["cost"][i][j],
        within=pyo.Reals,
    )

    model.shipment = pyo.Var(
        model.origins,
        model.destinations,
        domain=pyo.NonNegativeReals,
    )

    def supply_rule(model, i):
        return (
            sum(model.shipment[i, j] for j in model.destinations)
            == model.supply[i]
        )

    def demand_rule(model, j):
        return (
            sum(model.shipment[i, j] for i in model.origins)
            == model.demand[j]
        )

    model.supply_balance = pyo.Constraint(model.origins, rule=supply_rule)
    model.demand_balance = pyo.Constraint(model.destinations, rule=demand_rule)

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
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}