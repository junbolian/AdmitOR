# IR: {
#   "sets": {"F": [0,1,2,3,4,5], "C": [0,1,2,3,4,5,6,7,8]},
#   "params": {
#     "fixed_cost[i]": "params['fixed_cost_' + str(i)], real, i in F",
#     "demand[j]": "params['demand_' + str(j)], nonnegative real, j in C",
#     "shipping_cost[i,j]": "params['shipping_cost_' + str(i) + '_' + str(j)], real, (i,j) in F x C",
#     "capacity[i]": "params['capacity_' + str(i)], nonnegative real, i in F"
#   },
#   "variables": {
#     "opened[i]": "binary, i in F",
#     "shipped[i,j]": "nonnegative continuous, (i,j) in F x C"
#   },
#   "constraints": [
#     "sum(shipped[i,j] for i in F) == demand[j], for each j in C",
#     "sum(shipped[i,j] for j in C) <= capacity[i] * opened[i], for each i in F"
#   ],
#   "objective": "minimize sum(fixed_cost[i]*opened[i] for i in F) + sum(shipping_cost[i,j]*shipped[i,j] for (i,j) in F x C)"
# }

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.F = pyo.Set(initialize=range(6), ordered=True)
    model.C = pyo.Set(initialize=range(9), ordered=True)

    model.fixed_cost = pyo.Param(
        model.F,
        initialize={i: params[f"fixed_cost_{i}"] for i in model.F},
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        model.C,
        initialize={j: params[f"demand_{j}"] for j in model.C},
        within=pyo.NonNegativeReals,
    )
    model.shipping_cost = pyo.Param(
        model.F,
        model.C,
        initialize={
            (i, j): params[f"shipping_cost_{i}_{j}"]
            for i in model.F
            for j in model.C
        },
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.F,
        initialize={i: params[f"capacity_{i}"] for i in model.F},
        within=pyo.NonNegativeReals,
    )

    model.opened = pyo.Var(model.F, domain=pyo.Binary)
    model.shipped = pyo.Var(model.F, model.C, domain=pyo.NonNegativeReals)

    def demand_rule(model, j):
        return (
            sum(model.shipped[i, j] for i in model.F)
            == model.demand[j]
        )

    model.demand_satisfaction = pyo.Constraint(model.C, rule=demand_rule)

    def capacity_rule(model, i):
        return (
            sum(model.shipped[i, j] for j in model.C)
            <= model.capacity[i] * model.opened[i]
        )

    model.facility_capacity = pyo.Constraint(model.F, rule=capacity_rule)

    model.total_cost = pyo.Objective(
        expr=(
            sum(model.fixed_cost[i] * model.opened[i] for i in model.F)
            + sum(
                model.shipping_cost[i, j] * model.shipped[i, j]
                for i in model.F
                for j in model.C
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
        return {"objective": None, "status": "no_objective"}

    return {"objective": obj_val, "status": "optimal"}