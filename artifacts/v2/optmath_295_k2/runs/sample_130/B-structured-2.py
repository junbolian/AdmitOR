# IR: {"sets":{"P":[0,1,2,3],"C":[0,1,2,3,4]},"params":{"capacity":"nonnegative[P]","demand":"nonnegative[C]","min_delivery":"positive[P]","cost":"real[P,C]"},"variables":{"x[P,C]":"continuous nonnegative","y[P,C]":"binary"},"constraints":["sum(x[i,j] for j in C) <= capacity[i] for i in P","sum(x[i,j] for i in P) >= demand[j] for j in C","sum(y[i,j] for i in P) >= 2 for j in C","x[i,j] >= min_delivery[i]*y[i,j] for i in P,j in C","x[i,j] <= capacity[i]*y[i,j] for i in P,j in C"],"objective":"minimize sum(cost[i,j]*x[i,j] for i in P,j in C)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    """Accept indexed capacity, demand, min_delivery, and nested cost data."""
    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, 3)
    model.C = pyo.RangeSet(0, 4)

    model.capacity = pyo.Param(
        model.P,
        initialize={i: params["capacity"][i] for i in model.P},
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.C,
        initialize={j: params["demand"][j] for j in model.C},
        within=pyo.NonNegativeReals,
    )
    model.min_delivery = pyo.Param(
        model.P,
        initialize={i: params["min_delivery"][i] for i in model.P},
        within=pyo.PositiveReals,
    )
    model.cost = pyo.Param(
        model.P,
        model.C,
        initialize={
            (i, j): params["cost"][i][j]
            for i in model.P
            for j in model.C
        },
        within=pyo.Reals,
    )

    model.x = pyo.Var(model.P, model.C, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.P, model.C, domain=pyo.Binary)

    def capacity_rule(model, i):
        return sum(model.x[i, j] for j in model.C) <= model.capacity[i]

    model.capacity_constraints = pyo.Constraint(model.P, rule=capacity_rule)

    def demand_rule(model, j):
        return sum(model.x[i, j] for i in model.P) >= model.demand[j]

    model.demand_constraints = pyo.Constraint(model.C, rule=demand_rule)

    def contributors_rule(model, j):
        return sum(model.y[i, j] for i in model.P) >= 2

    model.contributor_constraints = pyo.Constraint(
        model.C, rule=contributors_rule
    )

    def minimum_delivery_rule(model, i, j):
        return model.x[i, j] >= model.min_delivery[i] * model.y[i, j]

    model.minimum_delivery_constraints = pyo.Constraint(
        model.P, model.C, rule=minimum_delivery_rule
    )

    def activation_rule(model, i, j):
        return model.x[i, j] <= model.capacity[i] * model.y[i, j]

    model.activation_constraints = pyo.Constraint(
        model.P, model.C, rule=activation_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[i, j] * model.x[i, j]
            for i in model.P
            for j in model.C
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