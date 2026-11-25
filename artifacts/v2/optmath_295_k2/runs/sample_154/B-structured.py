# IR: {"sets":{"I":"0..6","J":"0..6"},"params":{"supply":"I -> nonnegative real","demand":"J -> nonnegative real","transport_cost":"I x J -> real"},"variables":{"shipment[i,j]":"nonnegative real"},"constraints":["For each i in I: sum(shipment[i,j] for j in J) = supply[i]","For each j in J: sum(shipment[i,j] for i in I) = demand[j]"],"objective":"Minimize sum(transport_cost[i,j] * shipment[i,j] for i in I, j in J)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply = params["supply"]
    demand = params["demand"]
    transport_cost = params["transport_cost"]

    model = pyo.ConcreteModel()
    model.origins = pyo.RangeSet(0, 6)
    model.destinations = pyo.RangeSet(0, 6)

    model.supply = pyo.Param(
        model.origins,
        initialize=lambda mod, i: supply[i],
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.destinations,
        initialize=lambda mod, j: demand[j],
        within=pyo.NonNegativeReals,
    )
    model.transport_cost = pyo.Param(
        model.origins,
        model.destinations,
        initialize=lambda mod, i, j: transport_cost[i][j],
        within=pyo.Reals,
    )

    model.shipment = pyo.Var(
        model.origins,
        model.destinations,
        domain=pyo.NonNegativeReals,
    )

    def supply_rule(mod, i):
        return (
            sum(mod.shipment[i, j] for j in mod.destinations)
            == mod.supply[i]
        )

    def demand_rule(mod, j):
        return (
            sum(mod.shipment[i, j] for i in mod.origins)
            == mod.demand[j]
        )

    model.supply_balance = pyo.Constraint(
        model.origins, rule=supply_rule
    )
    model.demand_balance = pyo.Constraint(
        model.destinations, rule=demand_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.transport_cost[i, j] * model.shipment[i, j]
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