# IR: {"sets":{"DC":"0..8","STORE":"0..7"},"params":{"opening_costs":"DC -> nonnegative real, from params","transport_costs":"DC x STORE -> nonnegative real, from params","demands":"STORE -> nonnegative real, from params","capacities":"DC -> nonnegative real, from params"},"variables":{"opened[dc]":"binary","shipped[dc,store]":"nonnegative real"},"constraints":["For each store: sum_dc shipped[dc,store] == demands[store]","For each dc: sum_store shipped[dc,store] <= capacities[dc] * opened[dc]"],"objective":"Minimize sum_dc opening_costs[dc]*opened[dc] + sum_dc,store transport_costs[dc,store]*shipped[dc,store]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    opening_costs = params["opening_costs"]
    transport_costs = params["transport_costs"]
    demands = params["demands"]
    capacities = params["capacities"]

    model = pyo.ConcreteModel()

    model.DC = pyo.RangeSet(0, 8)
    model.STORE = pyo.RangeSet(0, 7)

    model.opening_cost = pyo.Param(
        model.DC,
        initialize=lambda mdl, dc: opening_costs[dc],
        within=pyo.NonNegativeReals,
    )
    model.transport_cost = pyo.Param(
        model.DC,
        model.STORE,
        initialize=lambda mdl, dc, store: transport_costs[dc][store],
        within=pyo.NonNegativeReals,
    )
    model.store_demand = pyo.Param(
        model.STORE,
        initialize=lambda mdl, store: demands[store],
        within=pyo.NonNegativeReals,
    )
    model.dc_capacity = pyo.Param(
        model.DC,
        initialize=lambda mdl, dc: capacities[dc],
        within=pyo.NonNegativeReals,
    )

    model.opened = pyo.Var(model.DC, domain=pyo.Binary)
    model.shipped = pyo.Var(
        model.DC, model.STORE, domain=pyo.NonNegativeReals
    )

    def demand_rule(mdl, store):
        return (
            sum(mdl.shipped[dc, store] for dc in mdl.DC)
            == mdl.store_demand[store]
        )

    model.demand_balance = pyo.Constraint(
        model.STORE, rule=demand_rule
    )

    def capacity_rule(mdl, dc):
        return (
            sum(mdl.shipped[dc, store] for store in mdl.STORE)
            <= mdl.dc_capacity[dc] * mdl.opened[dc]
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
                * model.shipped[dc, store]
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