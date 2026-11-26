# IR: {"sets":{"DC":[0,1,2,3],"STORE":[0,1,2,3,4,5]},"params":{"opening_cost":"DC -> nonnegative real","transport_cost":"DC x STORE -> nonnegative real; row-major nested 4x6 or flat length 24","demand":"STORE -> nonnegative real","capacity":"DC -> nonnegative real"},"variables":{"opened":"DC -> binary","shipment":"DC x STORE -> nonnegative continuous"},"constraints":["For each store j: sum_i shipment[i,j] = demand[j].","For each center i: sum_j shipment[i,j] <= capacity[i] * opened[i]."],"objective":"Minimize sum_i opening_cost[i]*opened[i] + sum_i,j transport_cost[i,j]*shipment[i,j]."}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()
    model.DC = pyo.RangeSet(0, 3)
    model.STORE = pyo.RangeSet(0, 5)

    flat_transport = len(transport_cost) == 24

    model.opening_cost = pyo.Param(
        model.DC,
        initialize={i: opening_cost[i] for i in model.DC},
        within=pyo.NonNegativeReals,
    )
    model.transport_cost = pyo.Param(
        model.DC,
        model.STORE,
        initialize={
            (i, j): (
                transport_cost[6 * i + j]
                if flat_transport
                else transport_cost[i][j]
            )
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

    def demand_rule(instance, j):
        return (
            sum(instance.shipment[i, j] for i in instance.DC)
            == instance.demand[j]
        )

    model.demand_fulfillment = pyo.Constraint(
        model.STORE, rule=demand_rule
    )

    def capacity_rule(instance, i):
        return (
            sum(instance.shipment[i, j] for j in instance.STORE)
            <= instance.capacity[i] * instance.opened[i]
        )

    model.capacity_limits = pyo.Constraint(
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
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}