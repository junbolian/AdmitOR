# IR: {"sets":{"W":[0,1,2,3,4],"S":[0,1,2,3,4,5],"P":[0,1]},"params":{"supply_product0":"W","supply_product1":"W","demand_product0":"S","demand_product1":"S","transport_cost_product0":"W x S","transport_cost_product1":"W x S","link_capacity":"W x S"},"variables":{"shipment[w,s,p]":"nonnegative continuous"},"constraints":["sum_s shipment[w,s,p] <= supply_product{p}[w] for each w,p","sum_w shipment[w,s,p] == demand_product{p}[s] for each s,p","sum_p shipment[w,s,p] <= link_capacity[w][s] for each w,s"],"objective":"minimize sum_{w,s,p} transport_cost_product{p}[w][s] * shipment[w,s,p]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supplies = {
        0: params["supply_product0"],
        1: params["supply_product1"],
    }
    demands = {
        0: params["demand_product0"],
        1: params["demand_product1"],
    }
    costs = {
        0: params["transport_cost_product0"],
        1: params["transport_cost_product1"],
    }
    capacities = params["link_capacity"]

    model = pyo.ConcreteModel()
    model.W = pyo.RangeSet(0, 4)
    model.S = pyo.RangeSet(0, 5)
    model.P = pyo.RangeSet(0, 1)

    model.supply = pyo.Param(
        model.W, model.P,
        initialize=lambda mdl, w, p: supplies[p][w],
    )
    model.demand = pyo.Param(
        model.S, model.P,
        initialize=lambda mdl, s, p: demands[p][s],
    )
    model.transport_cost = pyo.Param(
        model.W, model.S, model.P,
        initialize=lambda mdl, w, s, p: costs[p][w][s],
    )
    model.capacity = pyo.Param(
        model.W, model.S,
        initialize=lambda mdl, w, s: capacities[w][s],
    )

    model.shipment = pyo.Var(
        model.W, model.S, model.P,
        domain=pyo.NonNegativeReals,
    )

    def supply_rule(mdl, w, p):
        return (
            sum(mdl.shipment[w, s, p] for s in mdl.S)
            <= mdl.supply[w, p]
        )

    def demand_rule(mdl, s, p):
        return (
            sum(mdl.shipment[w, s, p] for w in mdl.W)
            == mdl.demand[s, p]
        )

    def capacity_rule(mdl, w, s):
        return (
            sum(mdl.shipment[w, s, p] for p in mdl.P)
            <= mdl.capacity[w, s]
        )

    model.supply_limits = pyo.Constraint(
        model.W, model.P, rule=supply_rule
    )
    model.demand_requirements = pyo.Constraint(
        model.S, model.P, rule=demand_rule
    )
    model.link_limits = pyo.Constraint(
        model.W, model.S, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.transport_cost[w, s, p] * model.shipment[w, s, p]
            for w in model.W
            for s in model.S
            for p in model.P
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