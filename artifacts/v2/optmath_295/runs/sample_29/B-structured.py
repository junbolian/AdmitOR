# IR: {"sets":{"F":[0,1,2,3,4],"C":[0,1,2,3,4,5,6]},"params":{"fixed_cost":"F -> real","shipping_cost":"F x C -> real","demand":"C -> nonnegative real","capacity":"F -> nonnegative real"},"variables":{"opened":"F -> binary","shipped":"F x C -> nonnegative real"},"constraints":["For each j in C: sum(i in F, shipped[i,j]) == demand[j]","For each i in F: sum(j in C, shipped[i,j]) <= capacity[i] * opened[i]"],"objective":"Minimize sum(i in F, fixed_cost[i]*opened[i]) + sum(i in F,j in C, shipping_cost[i,j]*shipped[i,j])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.F = pyo.RangeSet(0, 4)
    model.C = pyo.RangeSet(0, 6)

    model.fixed_cost = pyo.Param(
        model.F,
        initialize={i: params["fixed_cost"][i] for i in model.F},
        within=pyo.Reals,
    )
    model.shipping_cost = pyo.Param(
        model.F,
        model.C,
        initialize={
            (i, j): params["shipping_cost"][i][j]
            for i in model.F
            for j in model.C
        },
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        model.C,
        initialize={j: params["demand"][j] for j in model.C},
        within=pyo.NonNegativeReals,
    )
    model.capacity = pyo.Param(
        model.F,
        initialize={i: params["capacity"][i] for i in model.F},
        within=pyo.NonNegativeReals,
    )

    model.opened = pyo.Var(model.F, domain=pyo.Binary)
    model.shipped = pyo.Var(model.F, model.C, domain=pyo.NonNegativeReals)

    def demand_rule(mod, j):
        return sum(mod.shipped[i, j] for i in mod.F) == mod.demand[j]

    model.demand_satisfaction = pyo.Constraint(model.C, rule=demand_rule)

    def capacity_rule(mod, i):
        return (
            sum(mod.shipped[i, j] for j in mod.C)
            <= mod.capacity[i] * mod.opened[i]
        )

    model.capacity_activation = pyo.Constraint(model.F, rule=capacity_rule)

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
        # HiGHS may raise when no feasible solution can be loaded.
        # Objective retrieval below is the sole success test.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}