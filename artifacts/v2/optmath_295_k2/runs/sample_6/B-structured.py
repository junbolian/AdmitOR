# IR: {"sets":{"W":"0..4","S":"0..5"},"params":{"warehouse_supply":"W -> nonnegative real","store_demand":"S -> nonnegative real","transport_cost":"W x S -> real","route_capacity":"W x S -> nonnegative real"},"variables":{"shipment[w,s]":"nonnegative continuous"},"constraints":["sum(s in S, shipment[w,s]) <= warehouse_supply[w] for w in W","sum(w in W, shipment[w,s]) == store_demand[s] for s in S","shipment[w,s] <= route_capacity[w,s] for (w,s) in W x S"],"objective":"minimize sum((w,s) in W x S, transport_cost[w,s]*shipment[w,s])"}

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
        model.W,
        model.S,
        domain=pyo.NonNegativeReals,
    )

    model.supply_limit = pyo.Constraint(
        model.W,
        rule=lambda mdl, w: (
            sum(mdl.shipment[w, s] for s in mdl.S)
            <= mdl.warehouse_supply[w]
        ),
    )

    model.demand_balance = pyo.Constraint(
        model.S,
        rule=lambda mdl, s: (
            sum(mdl.shipment[w, s] for w in mdl.W)
            == mdl.store_demand[s]
        ),
    )

    model.route_limit = pyo.Constraint(
        model.W,
        model.S,
        rule=lambda mdl, w, s: (
            mdl.shipment[w, s] <= mdl.route_capacity[w, s]
        ),
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
        # Appsi raises this error when it cannot load a feasible solution.
        # Unexpected solver errors propagate.
        if "a feasible solution was not found" not in str(exc).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}