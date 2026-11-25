# IR: {"sets":{"facilities":[0,1,2,3],"customers":[0,1,2,3,4,5]},"params":{"fixed_cost":"real[facilities]","capacity":"nonnegative_real[facilities]","demand":"nonnegative_real[customers]","ship_cost":"real[facilities,customers]"},"variables":{"opened":"binary[facilities]","shipment":"nonnegative_real[facilities,customers]"},"constraints":["For each customer j: sum_i shipment[i,j] = demand[j]","For each facility i: sum_j shipment[i,j] <= capacity[i] * opened[i]"],"objective":"Minimize sum_i fixed_cost[i]*opened[i] + sum_i sum_j ship_cost[i,j]*shipment[i,j]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.facilities = pyo.RangeSet(0, 3)
    model.customers = pyo.RangeSet(0, 5)

    model.fixed_cost = pyo.Param(
        model.facilities,
        initialize={i: params["fixed_cost"][i] for i in model.facilities},
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.facilities,
        initialize={i: params["capacity"][i] for i in model.facilities},
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.customers,
        initialize={j: params["demand"][j] for j in model.customers},
        within=pyo.NonNegativeReals,
    )
    model.ship_cost = pyo.Param(
        model.facilities,
        model.customers,
        initialize={
            (i, j): params["ship_cost"][i][j]
            for i in model.facilities
            for j in model.customers
        },
        within=pyo.Reals,
    )

    model.opened = pyo.Var(model.facilities, domain=pyo.Binary)
    model.shipment = pyo.Var(
        model.facilities,
        model.customers,
        domain=pyo.NonNegativeReals,
    )

    def demand_rule(mod, j):
        return (
            sum(mod.shipment[i, j] for i in mod.facilities)
            == mod.demand[j]
        )

    model.demand_balance = pyo.Constraint(
        model.customers,
        rule=demand_rule,
    )

    def capacity_rule(mod, i):
        return (
            sum(mod.shipment[i, j] for j in mod.customers)
            <= mod.capacity[i] * mod.opened[i]
        )

    model.facility_capacity = pyo.Constraint(
        model.facilities,
        rule=capacity_rule,
    )

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.fixed_cost[i] * model.opened[i]
                for i in model.facilities
            )
            + sum(
                model.ship_cost[i, j] * model.shipment[i, j]
                for i in model.facilities
                for j in model.customers
            )
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