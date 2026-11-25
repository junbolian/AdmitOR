# IR: {"sets":{"J":"facilities 0..4","I":"customers 0..8"},"params":{"fixed_cost":"fixed_cost[j] from params","capacity":"capacity[j] from params","demand":"demand[i] from params","shipping_cost":"shipping_cost[i][j] from params"},"variables":{"opened[j]":"binary","shipment[i,j]":"nonnegative continuous"},"constraints":["For each i: sum_j shipment[i,j] = demand[i]","For each j: sum_i shipment[i,j] <= capacity[j] * opened[j]"],"objective":"Minimize sum_j fixed_cost[j]*opened[j] + sum_i sum_j shipping_cost[i][j]*shipment[i,j]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.J = pyo.RangeSet(0, 4)
    model.I = pyo.RangeSet(0, 8)

    model.fixed_cost = pyo.Param(
        model.J,
        initialize={j: params["fixed_cost"][j] for j in model.J},
    )
    model.capacity = pyo.Param(
        model.J,
        initialize={j: params["capacity"][j] for j in model.J},
    )
    model.demand = pyo.Param(
        model.I,
        initialize={i: params["demand"][i] for i in model.I},
    )
    model.shipping_cost = pyo.Param(
        model.I,
        model.J,
        initialize={
            (i, j): params["shipping_cost"][i][j]
            for i in model.I
            for j in model.J
        },
    )

    model.opened = pyo.Var(model.J, domain=pyo.Binary)
    model.shipment = pyo.Var(model.I, model.J, domain=pyo.NonNegativeReals)

    def demand_rule(model, i):
        return (
            sum(model.shipment[i, j] for j in model.J)
            == model.demand[i]
        )

    model.demand_satisfaction = pyo.Constraint(model.I, rule=demand_rule)

    def capacity_rule(model, j):
        return (
            sum(model.shipment[i, j] for i in model.I)
            <= model.capacity[j] * model.opened[j]
        )

    model.facility_capacity = pyo.Constraint(model.J, rule=capacity_rule)

    model.total_cost = pyo.Objective(
        expr=(
            sum(model.fixed_cost[j] * model.opened[j] for j in model.J)
            + sum(
                model.shipping_cost[i, j] * model.shipment[i, j]
                for i in model.I
                for j in model.J
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