# IR: {"sets":{"DC":"0..7","STORE":"0..4"},"params":{"opening_cost":"DC -> nonnegative real, from params","transport_cost":"DC x STORE -> nonnegative real, from params","demand":"STORE -> nonnegative real, from params","capacity":"DC -> nonnegative real, from params"},"variables":{"opened":"DC -> binary","shipment":"DC x STORE -> nonnegative real"},"constraints":["For each store j: sum_i shipment[i,j] = demand[j]","For each DC i: sum_j shipment[i,j] <= capacity[i] * opened[i]"],"objective":"Minimize sum_i opening_cost[i]*opened[i] + sum_i,j transport_cost[i,j]*shipment[i,j]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()

    model.DC = pyo.RangeSet(0, 7)
    model.STORE = pyo.RangeSet(0, 4)

    model.opening_cost = pyo.Param(
        model.DC,
        initialize={i: opening_cost[i] for i in model.DC},
        within=pyo.NonNegativeReals,
    )
    model.transport_cost = pyo.Param(
        model.DC,
        model.STORE,
        initialize={
            (i, j): transport_cost[i][j]
            for i in model.DC
            for j in model.STORE
        },
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.STORE,
        initialize={j: demand[j] for j in model.STORE},
        within=pyo.NonNegativeReals,
    )
    model.capacity = pyo.Param(
        model.DC,
        initialize={i: capacity[i] for i in model.DC},
        within=pyo.NonNegativeReals,
    )

    model.opened = pyo.Var(model.DC, domain=pyo.Binary)
    model.shipment = pyo.Var(
        model.DC, model.STORE, domain=pyo.NonNegativeReals
    )

    def demand_rule(mdl, j):
        return (
            sum(mdl.shipment[i, j] for i in mdl.DC)
            == mdl.demand[j]
        )

    model.demand_balance = pyo.Constraint(
        model.STORE, rule=demand_rule
    )

    def capacity_rule(mdl, i):
        return (
            sum(mdl.shipment[i, j] for j in mdl.STORE)
            <= mdl.capacity[i] * mdl.opened[i]
        )

    model.capacity_limit = pyo.Constraint(
        model.DC, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.opening_cost[i] * model.opened[i]
                for i in model.DC
            )
            + sum(
                model.transport_cost[i, j] * model.shipment[i, j]
                for i in model.DC
                for j in model.STORE
            )
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
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}