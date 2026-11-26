# IR: {"sets":{"C":[0,1,2,3,4,5],"S":[0,1,2,3,4]},"params":{"opening_cost":"C -> dollars, from params['opening_cost']","transport_cost":"C x S -> dollars/unit, from params['transport_cost']","demand":"S -> units, from params['demand']","capacity":"C -> units, from params['capacity']"},"variables":{"opened[c]":"binary","shipped[c,s]":"nonnegative continuous"},"constraints":["For each s in S: sum(shipped[c,s] for c in C) == demand[s]","For each c in C: sum(shipped[c,s] for s in S) <= capacity[c] * opened[c]"],"objective":"minimize sum(opening_cost[c] * opened[c] for c in C) + sum(transport_cost[c,s] * shipped[c,s] for c in C, s in S)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Solve using zero-based sequences and a center-by-store cost matrix."""
    model = pyo.ConcreteModel()

    model.C = pyo.RangeSet(0, 5)
    model.S = pyo.RangeSet(0, 4)

    model.opening_cost = pyo.Param(
        model.C,
        initialize={c: params["opening_cost"][c] for c in model.C},
        within=pyo.Reals,
    )
    model.transport_cost = pyo.Param(
        model.C,
        model.S,
        initialize={
            (c, s): params["transport_cost"][c][s]
            for c in model.C
            for s in model.S
        },
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        model.S,
        initialize={s: params["demand"][s] for s in model.S},
        within=pyo.NonNegativeReals,
    )
    model.capacity = pyo.Param(
        model.C,
        initialize={c: params["capacity"][c] for c in model.C},
        within=pyo.NonNegativeReals,
    )

    model.opened = pyo.Var(model.C, domain=pyo.Binary)
    model.shipped = pyo.Var(model.C, model.S, domain=pyo.NonNegativeReals)

    def demand_rule(instance, s):
        return (
            sum(instance.shipped[c, s] for c in instance.C)
            == instance.demand[s]
        )

    model.demand_balance = pyo.Constraint(model.S, rule=demand_rule)

    def capacity_rule(instance, c):
        return (
            sum(instance.shipped[c, s] for s in instance.S)
            <= instance.capacity[c] * instance.opened[c]
        )

    model.capacity_limit = pyo.Constraint(model.C, rule=capacity_rule)

    model.total_cost = pyo.Objective(
        expr=(
            sum(model.opening_cost[c] * model.opened[c] for c in model.C)
            + sum(
                model.transport_cost[c, s] * model.shipped[c, s]
                for c in model.C
                for s in model.S
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
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}