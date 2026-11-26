# IR: {"sets":{"DC":[0,1,2,3,4,5],"STORE":[0,1,2,3,4,5,6,7,8]},"params":{"opening_cost":"DC -> nonnegative real","transport_cost":"DC x STORE -> nonnegative real","demand":"STORE -> nonnegative real","capacity":"DC -> nonnegative real"},"variables":{"opened[dc]":"binary","shipment[dc,store]":"nonnegative continuous"},"constraints":["For each store: sum_dc shipment[dc,store] = demand[store]","For each dc: sum_store shipment[dc,store] <= capacity[dc] * opened[dc]"],"objective":"Minimize sum_dc opening_cost[dc]*opened[dc] + sum_dc,store transport_cost[dc,store]*shipment[dc,store]"}
#
# Input convention: opening_cost, demand, and capacity are zero-based
# sequences; transport_cost is a zero-based sequence of six rows,
# each containing nine transportation costs.

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()

    model.DC = pyo.RangeSet(0, 5)
    model.STORE = pyo.RangeSet(0, 8)

    model.opening_cost = pyo.Param(
        model.DC,
        initialize=lambda mdl, dc: opening_cost[dc],
        within=pyo.NonNegativeReals,
    )
    model.transport_cost = pyo.Param(
        model.DC,
        model.STORE,
        initialize=lambda mdl, dc, store: transport_cost[dc][store],
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.STORE,
        initialize=lambda mdl, store: demand[store],
        within=pyo.NonNegativeReals,
    )
    model.capacity = pyo.Param(
        model.DC,
        initialize=lambda mdl, dc: capacity[dc],
        within=pyo.NonNegativeReals,
    )

    model.opened = pyo.Var(model.DC, domain=pyo.Binary)
    model.shipment = pyo.Var(
        model.DC, model.STORE, domain=pyo.NonNegativeReals
    )

    def demand_rule(mdl, store):
        return (
            sum(mdl.shipment[dc, store] for dc in mdl.DC)
            == mdl.demand[store]
        )

    model.demand_balance = pyo.Constraint(
        model.STORE, rule=demand_rule
    )

    def capacity_rule(mdl, dc):
        return (
            sum(mdl.shipment[dc, store] for store in mdl.STORE)
            <= mdl.capacity[dc] * mdl.opened[dc]
        )

    model.capacity_limit = pyo.Constraint(
        model.DC, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.opening_cost[dc] * model.opened[dc]
                for dc in model.DC
            )
            + sum(
                model.transport_cost[dc, store]
                * model.shipment[dc, store]
                for dc in model.DC
                for store in model.STORE
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
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}