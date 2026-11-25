# IR: {"sets":{"DC":"0..6","STORE":"0..7"},"params":{"fixed_cost":"fixed_cost[DC]","shipping_cost":"shipping_cost[DC][STORE]","demand":"demand[STORE]","capacity":"capacity[DC]"},"variables":{"opened[DC]":"binary","shipment[DC,STORE]":"continuous, nonnegative"},"constraints":["For each store j: sum_i shipment[i,j] == demand[j]","For each DC i: sum_j shipment[i,j] <= capacity[i]*opened[i]"],"objective":"Minimize sum_i fixed_cost[i]*opened[i] + sum_i,j shipping_cost[i][j]*shipment[i,j]"}
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

    def demand_rule(instance, j):
        return (
            sum(instance.shipment[i, j] for i in instance.DC)
            == instance.demand[j]
        )

    model.demand_balance = pyo.Constraint(
        model.STORE, rule=demand_rule
    )

    def capacity_rule(instance, i):
        return (
            sum(instance.shipment[i, j] for j in instance.STORE)
            <= instance.capacity[i] * instance.opened[i]
        )

    model.capacity_limit = pyo.Constraint(
        model.DC, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.fixed_cost[i] * model.opened[i]
                for i in model.DC
            )
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
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}