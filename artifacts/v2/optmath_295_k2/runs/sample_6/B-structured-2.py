# IR: {"sets":{"W":"0..4","S":"0..5"},"params":{"warehouse_supply":"nonnegative[W]","store_demand":"nonnegative[S]","transport_cost":"real[W,S]","route_capacity":"nonnegative[W,S]"},"variables":{"shipment[W,S]":"continuous, nonnegative"},"constraints":["sum(shipment[w,s] for s in S) <= warehouse_supply[w] for w in W","sum(shipment[w,s] for w in W) == store_demand[s] for s in S","shipment[w,s] <= route_capacity[w,s] for (w,s) in W x S"],"objective":"minimize sum(transport_cost[w,s] * shipment[w,s] for (w,s) in W x S)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using indexed vectors and nested matrices supplied in params."""
    warehouse_supply = params["warehouse_supply"]
    store_demand = params["store_demand"]
    transport_cost = params["transport_cost"]
    route_capacity = params["route_capacity"]

    model = pyo.ConcreteModel()
    model.W = pyo.RangeSet(0, 4)
    model.S = pyo.RangeSet(0, 5)

    model.warehouse_supply = pyo.Param(
        model.W,
        initialize=lambda mdl, w: warehouse_supply[w],
        within=pyo.NonNegativeReals,
    )
    model.store_demand = pyo.Param(
        model.S,
        initialize=lambda mdl, s: store_demand[s],
        within=pyo.NonNegativeReals,
    )
    model.transport_cost = pyo.Param(
        model.W,
        model.S,
        initialize=lambda mdl, w, s: transport_cost[w][s],
        within=pyo.Reals,
    )
    model.route_capacity = pyo.Param(
        model.W,
        model.S,
        initialize=lambda mdl, w, s: route_capacity[w][s],
        within=pyo.NonNegativeReals,
    )

    model.shipment = pyo.Var(
        model.W, model.S, domain=pyo.NonNegativeReals
    )

    def supply_rule(mdl, w):
        return (
            sum(mdl.shipment[w, s] for s in mdl.S)
            <= mdl.warehouse_supply[w]
        )

    def demand_rule(mdl, s):
        return (
            sum(mdl.shipment[w, s] for w in mdl.W)
            == mdl.store_demand[s]
        )

    def capacity_rule(mdl, w, s):
        return mdl.shipment[w, s] <= mdl.route_capacity[w, s]

    model.supply_limit = pyo.Constraint(model.W, rule=supply_rule)
    model.demand_balance = pyo.Constraint(model.S, rule=demand_rule)
    model.route_limit = pyo.Constraint(
        model.W, model.S, rule=capacity_rule
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
    except RuntimeError as exc:
        # APPsi raises this when it cannot load a feasible solution.
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}