# IR: {"sets":{"origins":[0,1,2,3,4],"destinations":[0,1,2,3,4,5]},"params":{"supply":"nonnegative[origins]","demand":"nonnegative[destinations]","cost":"real[origins,destinations]","capacity":"nonnegative[origins,destinations]"},"variables":{"shipment":"continuous nonnegative[origins,destinations]"},"constraints":["sum(shipment[i,j] for j in destinations) == supply[i] for each origin i","sum(shipment[i,j] for i in origins) == demand[j] for each destination j","shipment[i,j] <= capacity[i,j] for each origin i and destination j"],"objective":"minimize sum(cost[i,j]*shipment[i,j] for i in origins for j in destinations)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.origins = pyo.RangeSet(0, 4)
    model.destinations = pyo.RangeSet(0, 5)

    model.supply = pyo.Param(
        model.origins,
        initialize={i: params["supply"][i] for i in model.origins},
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.destinations,
        initialize={j: params["demand"][j] for j in model.destinations},
        within=pyo.NonNegativeReals,
    )
    model.cost = pyo.Param(
        model.origins,
        model.destinations,
        initialize={
            (i, j): params["cost"][i][j]
            for i in model.origins
            for j in model.destinations
        },
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.origins,
        model.destinations,
        initialize={
            (i, j): params["capacity"][i][j]
            for i in model.origins
            for j in model.destinations
        },
        within=pyo.NonNegativeReals,
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

    model.supply_balance = pyo.Constraint(
        model.origins, rule=supply_rule
    )

    def demand_rule(mod, j):
        return (
            sum(mod.shipment[i, j] for i in mod.origins)
            == mod.demand[j]
        )

    model.demand_balance = pyo.Constraint(
        model.destinations, rule=demand_rule
    )

    def capacity_rule(mod, i, j):
        return mod.shipment[i, j] <= mod.capacity[i, j]

    model.link_limits = pyo.Constraint(
        model.origins,
        model.destinations,
        rule=capacity_rule,
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
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}