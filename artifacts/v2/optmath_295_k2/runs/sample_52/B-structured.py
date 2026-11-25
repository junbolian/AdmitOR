# IR: {"sets":{"F":[0,1,2,3],"C":[0,1,2,3,4,5,6,7,8,9]},"params":{"fixed_cost":"real[F]","demand":"nonnegative_real[C]","capacity":"nonnegative_real[F]","variable_cost":"real[F,C]"},"variables":{"opened":"binary[F]","shipped":"nonnegative_real[F,C]"},"constraints":["forall j in C: sum(i in F, shipped[i,j]) == demand[j]","forall i in F: sum(j in C, shipped[i,j]) <= capacity[i] * opened[i]"],"objective":"minimize sum(i in F, fixed_cost[i]*opened[i]) + sum(i in F,j in C, variable_cost[i,j]*shipped[i,j])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.F = pyo.RangeSet(0, 3)
    model.C = pyo.RangeSet(0, 9)

    model.fixed_cost = pyo.Param(
        model.F,
        initialize={i: params["fixed_cost"][i] for i in model.F},
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
    model.variable_cost = pyo.Param(
        model.F,
        model.C,
        initialize={
            (i, j): params["variable_cost"][i][j]
            for i in model.F
            for j in model.C
        },
        within=pyo.Reals,
    )

    model.opened = pyo.Var(model.F, domain=pyo.Binary)
    model.shipped = pyo.Var(model.F, model.C, domain=pyo.NonNegativeReals)

    def demand_rule(instance, j):
        return (
            sum(instance.shipped[i, j] for i in instance.F)
            == instance.demand[j]
        )

    model.demand_satisfaction = pyo.Constraint(model.C, rule=demand_rule)

    def capacity_rule(instance, i):
        return (
            sum(instance.shipped[i, j] for j in instance.C)
            <= instance.capacity[i] * instance.opened[i]
        )

    model.capacity_link = pyo.Constraint(model.F, rule=capacity_rule)

    model.total_cost = pyo.Objective(
        expr=(
            sum(model.fixed_cost[i] * model.opened[i] for i in model.F)
            + sum(
                model.variable_cost[i, j] * model.shipped[i, j]
                for i in model.F
                for j in model.C
            )
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}