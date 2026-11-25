# IR: {"sets":{"W":"0..7","S":"0..5"},"params":{"supplies":"nonnegative vector indexed by W","demands":"nonnegative vector indexed by S","transport_costs":"real matrix indexed by W,S","capacities":"nonnegative matrix indexed by W,S"},"variables":{"shipment[w,s]":"nonnegative continuous"},"constraints":["sum_s shipment[w,s] = supplies[w] for each w in W","sum_w shipment[w,s] = demands[s] for each s in S","shipment[w,s] <= capacities[w,s] for each (w,s) in W x S"],"objective":"minimize sum_(w,s) transport_costs[w,s] * shipment[w,s]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supplies = params["supplies"]
    demands = params["demands"]
    transport_costs = params["transport_costs"]
    capacities = params["capacities"]

    model = pyo.ConcreteModel()

    model.warehouses = pyo.RangeSet(0, 7)
    model.stores = pyo.RangeSet(0, 5)

    model.supply_amount = pyo.Param(
        model.warehouses,
        initialize=lambda mdl, w: supplies[w],
        within=pyo.NonNegativeReals,
    )
    model.demand_amount = pyo.Param(
        model.stores,
        initialize=lambda mdl, s: demands[s],
        within=pyo.NonNegativeReals,
    )
    model.unit_cost = pyo.Param(
        model.warehouses,
        model.stores,
        initialize=lambda mdl, w, s: transport_costs[w][s],
        within=pyo.Reals,
    )
    model.route_capacity = pyo.Param(
        model.warehouses,
        model.stores,
        initialize=lambda mdl, w, s: capacities[w][s],
        within=pyo.NonNegativeReals,
    )

    model.shipment = pyo.Var(
        model.warehouses,
        model.stores,
        domain=pyo.NonNegativeReals,
    )

    def supply_rule(mdl, w):
        return (
            sum(mdl.shipment[w, s] for s in mdl.stores)
            == mdl.supply_amount[w]
        )

    model.supply_balance = pyo.Constraint(
        model.warehouses, rule=supply_rule
    )

    def demand_rule(mdl, s):
        return (
            sum(mdl.shipment[w, s] for w in mdl.warehouses)
            == mdl.demand_amount[s]
        )

    model.demand_balance = pyo.Constraint(
        model.stores, rule=demand_rule
    )

    def capacity_rule(mdl, w, s):
        return mdl.shipment[w, s] <= mdl.route_capacity[w, s]

    model.capacity_limits = pyo.Constraint(
        model.warehouses,
        model.stores,
        rule=capacity_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.unit_cost[w, s] * model.shipment[w, s]
            for w in model.warehouses
            for s in model.stores
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