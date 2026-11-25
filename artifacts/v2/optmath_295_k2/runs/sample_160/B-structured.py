# IR: {"sets":{"DC":"0..6","STORE":"0..7"},"params":{"fixed_cost":"fixed_cost[i]","shipping_cost":"shipping_cost[i][j]","demand":"demand[j]","capacity":"capacity[i]"},"variables":{"opened[i]":"Binary","shipment[i,j]":"NonNegativeReals"},"constraints":["demand_balance[j]: sum(i in DC, shipment[i,j]) == demand[j]","capacity_link[i]: sum(j in STORE, shipment[i,j]) <= capacity[i]*opened[i]"],"objective":"minimize sum(i in DC, fixed_cost[i]*opened[i]) + sum(i in DC,j in STORE, shipping_cost[i][j]*shipment[i,j])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.DC = pyo.RangeSet(0, 6)
    model.STORE = pyo.RangeSet(0, 7)

    model.fixed_cost = pyo.Param(
        model.DC,
        initialize={i: params["fixed_cost"][i] for i in model.DC},
    )
    model.shipping_cost = pyo.Param(
        model.DC,
        model.STORE,
        initialize={
            (i, j): params["shipping_cost"][i][j]
            for i in model.DC
            for j in model.STORE
        },
    )
    model.demand = pyo.Param(
        model.STORE,
        initialize={j: params["demand"][j] for j in model.STORE},
    )
    model.capacity = pyo.Param(
        model.DC,
        initialize={i: params["capacity"][i] for i in model.DC},
    )

    model.opened = pyo.Var(model.DC, domain=pyo.Binary)
    model.shipment = pyo.Var(
        model.DC, model.STORE, domain=pyo.NonNegativeReals
    )

    def demand_balance_rule(instance, j):
        return (
            sum(instance.shipment[i, j] for i in instance.DC)
            == instance.demand[j]
        )

    model.demand_balance = pyo.Constraint(
        model.STORE, rule=demand_balance_rule
    )

    def capacity_link_rule(instance, i):
        return (
            sum(instance.shipment[i, j] for j in instance.STORE)
            <= instance.capacity[i] * instance.opened[i]
        )

    model.capacity_link = pyo.Constraint(
        model.DC, rule=capacity_link_rule
    )

    model.total_cost = pyo.Objective(
        expr=(
            sum(model.fixed_cost[i] * model.opened[i] for i in model.DC)
            + sum(
                model.shipping_cost[i, j] * model.shipment[i, j]
                for i in model.DC
                for j in model.STORE
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