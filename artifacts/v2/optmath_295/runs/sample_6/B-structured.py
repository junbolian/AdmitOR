# IR: {"sets":{"W":"0..4","S":"0..5"},"params":{"warehouse_supply":"nonnegative[W]","store_demand":"nonnegative[S]","transport_cost":"real[W,S]","route_capacity":"nonnegative[W,S]"},"variables":{"shipment":"nonnegative continuous[W,S]"},"constraints":["sum(s in S, shipment[w,s]) <= warehouse_supply[w] for w in W","sum(w in W, shipment[w,s]) == store_demand[s] for s in S","shipment[w,s] <= route_capacity[w,s] for (w,s) in W x S"],"objective":"minimize sum((w,s) in W x S, transport_cost[w,s] * shipment[w,s])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    warehouse_supply = params["warehouse_supply"]
    store_demand = params["store_demand"]
    transport_cost = params["transport_cost"]
    route_capacity = params["route_capacity"]

    model = pyo.ConcreteModel()

    model.W = pyo.RangeSet(0, 4)
    model.S = pyo.RangeSet(0, 5)

    model.warehouse_supply = pyo.Param(
        model.W,
        initialize={w: warehouse_supply[w] for w in model.W},
        within=pyo.NonNegativeReals,
    )
    model.store_demand = pyo.Param(
        model.S,
        initialize={s: store_demand[s] for s in model.S},
        within=pyo.NonNegativeReals,
    )
    model.transport_cost = pyo.Param(
        model.W,
        model.S,
        initialize={
            (w, s): transport_cost[w][s]
            for w in model.W
            for s in model.S
        },
        within=pyo.Reals,
    )
    model.route_capacity = pyo.Param(
        model.W,
        model.S,
        initialize={
            (w, s): route_capacity[w][s]
            for w in model.W
            for s in model.S
        },
        within=pyo.NonNegativeReals,
    )

    model.shipment = pyo.Var(
        model.W, model.S, domain=pyo.NonNegativeReals
    )

    def supply_rule(current_model, w):
        return (
            sum(current_model.shipment[w, s] for s in current_model.S)
            <= current_model.warehouse_supply[w]
        )

    def demand_rule(current_model, s):
        return (
            sum(current_model.shipment[w, s] for w in current_model.W)
            == current_model.store_demand[s]
        )

    def route_rule(current_model, w, s):
        return (
            current_model.shipment[w, s]
            <= current_model.route_capacity[w, s]
        )

    model.supply_constraints = pyo.Constraint(model.W, rule=supply_rule)
    model.demand_constraints = pyo.Constraint(model.S, rule=demand_rule)
    model.route_constraints = pyo.Constraint(
        model.W, model.S, rule=route_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.transport_cost[w, s] * model.shipment[w, s]
            for w in model.W
            for s in model.S
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