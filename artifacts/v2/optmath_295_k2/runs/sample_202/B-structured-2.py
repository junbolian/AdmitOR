# IR: {"sets":{"F":[0,1,2,3,4,5],"C":[0,1,2,3,4,5,6,7,8]},"params":{"fixed_cost[i]":"params['fixed_cost_'+str(i)], real, i in F","demand[j]":"params['demand_'+str(j)], nonnegative real, j in C","shipping_cost[i,j]":"params['shipping_cost_'+str(i)+'_'+str(j)], real, (i,j) in F x C","capacity[i]":"params['capacity_'+str(i)], nonnegative real, i in F"},"variables":{"open_facility[i]":"binary, i in F","shipment[i,j]":"nonnegative continuous, (i,j) in F x C"},"constraints":["sum(i in F, shipment[i,j]) = demand[j], j in C","sum(j in C, shipment[i,j]) <= capacity[i] * open_facility[i], i in F"],"objective":{"sense":"minimize","expression":"sum(i in F, fixed_cost[i]*open_facility[i]) + sum((i,j) in F x C, shipping_cost[i,j]*shipment[i,j])"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.F = pyo.RangeSet(0, 5)
    model.C = pyo.RangeSet(0, 8)

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

    model.open_facility = pyo.Var(model.F, domain=pyo.Binary)
    model.shipment = pyo.Var(
        model.F, model.C, domain=pyo.NonNegativeReals
    )

    def demand_rule(model, j):
        return (
            sum(model.shipment[i, j] for i in model.F)
            == model.demand[j]
        )

    model.demand_satisfaction = pyo.Constraint(
        model.C, rule=demand_rule
    )

    def capacity_rule(model, i):
        return (
            sum(model.shipment[i, j] for j in model.C)
            <= model.capacity[i] * model.open_facility[i]
        )

    model.facility_capacity = pyo.Constraint(
        model.F, rule=capacity_rule
    )

    model.total_cost = pyo.Objective(
        expr=(
            sum(
                model.fixed_cost[i] * model.open_facility[i]
                for i in model.F
            )
            + sum(
                model.shipping_cost[i, j] * model.shipment[i, j]
                for i in model.F
                for j in model.C
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