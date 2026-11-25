# {"sets":{"F":"0..4","C":"0..9"},"params":{"fixed_cost":"F -> real","demand":"C -> nonnegative real","shipping_cost":"F x C -> real","capacity":"F -> nonnegative real"},"variables":{"opened":"F -> binary","shipped":"F x C -> nonnegative real"},"constraints":["For each j in C: sum(i in F, shipped[i,j]) = demand[j]","For each i in F: sum(j in C, shipped[i,j]) <= capacity[i]*opened[i]"],"objective":"minimize sum(i in F, fixed_cost[i]*opened[i]) + sum(i in F,j in C, shipping_cost[i,j]*shipped[i,j])"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    fixed_cost = params["fixed_cost"]
    demand = params["demand"]
    shipping_cost = params["shipping_cost"]
    capacity = params["capacity"]

    model = pyo.ConcreteModel()
    model.F = pyo.RangeSet(0, 4)
    model.C = pyo.RangeSet(0, 9)

    model.fixed_cost = pyo.Param(
        model.F, initialize=lambda mdl, i: fixed_cost[i], within=pyo.Reals
    )
    model.demand = pyo.Param(
        model.C, initialize=lambda mdl, j: demand[j], within=pyo.NonNegativeReals
    )
    model.shipping_cost = pyo.Param(
        model.F,
        model.C,
        initialize=lambda mdl, i, j: shipping_cost[i][j],
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.F, initialize=lambda mdl, i: capacity[i], within=pyo.NonNegativeReals
    )

    model.opened = pyo.Var(model.F, domain=pyo.Binary)
    model.shipped = pyo.Var(model.F, model.C, domain=pyo.NonNegativeReals)

    def demand_rule(mdl, j):
        return sum(mdl.shipped[i, j] for i in mdl.F) == mdl.demand[j]

    model.demand_satisfaction = pyo.Constraint(model.C, rule=demand_rule)

    def capacity_rule(mdl, i):
        return (
            sum(mdl.shipped[i, j] for j in mdl.C)
            <= mdl.capacity[i] * mdl.opened[i]
        )

    model.capacity_activation = pyo.Constraint(model.F, rule=capacity_rule)

    model.total_cost = pyo.Objective(
        expr=sum(model.fixed_cost[i] * model.opened[i] for i in model.F)
        + sum(
            model.shipping_cost[i, j] * model.shipped[i, j]
            for i in model.F
            for j in model.C
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