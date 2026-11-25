# IR: {"sets":{"F":[0,1,2,3],"C":[0,1,2,3,4,5,6,7]},"params":{"fixed_cost":"F -> real","capacity":"F -> nonnegative real","demand":"C -> nonnegative real","shipping_cost":"F x C -> real"},"variables":{"opened[f]":"binary, f in F","shipment[f,c]":"nonnegative continuous, (f,c) in F x C"},"constraints":["sum(shipment[f,c] for f in F) == demand[c], for c in C","sum(shipment[f,c] for c in C) <= capacity[f]*opened[f], for f in F"],"objective":"minimize sum(fixed_cost[f]*opened[f] for f in F) + sum(shipping_cost[f,c]*shipment[f,c] for f in F,c in C)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    fixed_cost = params["fixed_cost"]
    capacity = params["capacity"]
    demand = params["demand"]
    shipping_cost = params["shipping_cost"]

    model = pyo.ConcreteModel()

    model.facilities = pyo.RangeSet(0, 3)
    model.customers = pyo.RangeSet(0, 7)

    model.fixed_cost = pyo.Param(
        model.facilities,
        initialize=lambda mdl, f: fixed_cost[f],
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.facilities,
        initialize=lambda mdl, f: capacity[f],
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.customers,
        initialize=lambda mdl, c: demand[c],
        within=pyo.NonNegativeReals,
    )
    model.shipping_cost = pyo.Param(
        model.facilities,
        model.customers,
        initialize=lambda mdl, f, c: shipping_cost[f][c],
        within=pyo.Reals,
    )

    model.opened = pyo.Var(model.facilities, domain=pyo.Binary)
    model.shipment = pyo.Var(
        model.facilities,
        model.customers,
        domain=pyo.NonNegativeReals,
    )

    def demand_rule(mdl, c):
        return (
            sum(mdl.shipment[f, c] for f in mdl.facilities)
            == mdl.demand[c]
        )

    model.demand_fulfillment = pyo.Constraint(
        model.customers,
        rule=demand_rule,
    )

    def capacity_rule(mdl, f):
        return (
            sum(mdl.shipment[f, c] for c in mdl.customers)
            <= mdl.capacity[f] * mdl.opened[f]
        )

    model.facility_capacity = pyo.Constraint(
        model.facilities,
        rule=capacity_rule,
    )

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.fixed_cost[f] * model.opened[f]
                for f in model.facilities
            )
            + sum(
                model.shipping_cost[f, c] * model.shipment[f, c]
                for f in model.facilities
                for c in model.customers
            )
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}