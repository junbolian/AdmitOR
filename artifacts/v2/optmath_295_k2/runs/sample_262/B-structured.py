# IR: {"sets":{"F":[0,1,2,3],"C":[0,1,2,3,4,5,6,7]},"params":{"fixed_cost":"F -> real","demand":"C -> nonnegative real","ship_cost":"F x C -> real","capacity":"F -> nonnegative real"},"variables":{"opened[f]":"binary","shipped[f,c]":"nonnegative continuous"},"constraints":["For each c in C: sum(f in F, shipped[f,c]) = demand[c]","For each f in F: sum(c in C, shipped[f,c]) <= capacity[f] * opened[f]"],"objective":"Minimize sum(f in F, fixed_cost[f]*opened[f]) + sum(f in F,c in C, ship_cost[f,c]*shipped[f,c])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.F = pyo.RangeSet(0, 3)
    model.C = pyo.RangeSet(0, 7)

    model.fixed_cost = pyo.Param(
        model.F,
        initialize={f: params["fixed_cost"][f] for f in model.F},
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        model.C,
        initialize={c: params["demand"][c] for c in model.C},
        within=pyo.NonNegativeReals,
    )
    model.ship_cost = pyo.Param(
        model.F,
        model.C,
        initialize={
            (f, c): params["ship_cost"][f][c]
            for f in model.F
            for c in model.C
        },
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.F,
        initialize={f: params["capacity"][f] for f in model.F},
        within=pyo.NonNegativeReals,
    )

    model.opened = pyo.Var(model.F, domain=pyo.Binary)
    model.shipped = pyo.Var(model.F, model.C, domain=pyo.NonNegativeReals)

    def demand_rule(model, c):
        return sum(model.shipped[f, c] for f in model.F) == model.demand[c]

    model.demand_fulfillment = pyo.Constraint(model.C, rule=demand_rule)

    def capacity_rule(model, f):
        return (
            sum(model.shipped[f, c] for c in model.C)
            <= model.capacity[f] * model.opened[f]
        )

    model.facility_capacity = pyo.Constraint(model.F, rule=capacity_rule)

    model.total_cost = pyo.Objective(
        expr=sum(model.fixed_cost[f] * model.opened[f] for f in model.F)
        + sum(
            model.ship_cost[f, c] * model.shipped[f, c]
            for f in model.F
            for c in model.C
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        # Infeasible solves may raise when HiGHS attempts to load a solution.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}