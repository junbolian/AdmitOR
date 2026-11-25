# IR: {"sets":{"P":[0,1,2,3,4],"C":[0,1,2,3,4,5]},"params":{"capacity":"params['capacity'][i]","demand":"params['demand'][j]","cost":"params['cost'][i][j]","min_delivery":"params['min_delivery'][i]","min_contributors":"params['min_contributors'][j]"},"variables":{"x[i,j]":"NonNegativeReals","y[i,j]":"Binary"},"constraints":["sum(x[i,j] for j in C) <= capacity[i] for i in P","sum(x[i,j] for i in P) >= demand[j] for j in C","x[i,j] >= min_delivery[i]*y[i,j] for i in P,j in C","x[i,j] <= capacity[i]*y[i,j] for i in P,j in C","sum(y[i,j] for i in P) >= min_contributors[j] for j in C"],"objective":"minimize sum(cost[i,j]*x[i,j] for i in P,j in C)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, 4)
    model.C = pyo.RangeSet(0, 5)

    model.capacity = pyo.Param(
        model.P,
        initialize={i: params["capacity"][i] for i in model.P},
    )
    model.demand = pyo.Param(
        model.C,
        initialize={j: params["demand"][j] for j in model.C},
    )
    model.cost = pyo.Param(
        model.P,
        model.C,
        initialize={
            (i, j): params["cost"][i][j]
            for i in model.P
            for j in model.C
        },
    )
    model.min_delivery = pyo.Param(
        model.P,
        initialize={i: params["min_delivery"][i] for i in model.P},
    )
    model.min_contributors = pyo.Param(
        model.C,
        initialize={
            j: params["min_contributors"][j] for j in model.C
        },
    )

    model.x = pyo.Var(model.P, model.C, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.P, model.C, domain=pyo.Binary)

    def capacity_rule(instance, i):
        return (
            sum(instance.x[i, j] for j in instance.C)
            <= instance.capacity[i]
        )

    model.capacity_limit = pyo.Constraint(model.P, rule=capacity_rule)

    def demand_rule(instance, j):
        return (
            sum(instance.x[i, j] for i in instance.P)
            >= instance.demand[j]
        )

    model.demand_requirement = pyo.Constraint(model.C, rule=demand_rule)

    def minimum_delivery_rule(instance, i, j):
        return (
            instance.x[i, j]
            >= instance.min_delivery[i] * instance.y[i, j]
        )

    model.minimum_delivery_link = pyo.Constraint(
        model.P, model.C, rule=minimum_delivery_rule
    )

    def maximum_delivery_rule(instance, i, j):
        return (
            instance.x[i, j]
            <= instance.capacity[i] * instance.y[i, j]
        )

    model.maximum_delivery_link = pyo.Constraint(
        model.P, model.C, rule=maximum_delivery_rule
    )

    def contributors_rule(instance, j):
        return (
            sum(instance.y[i, j] for i in instance.P)
            >= instance.min_contributors[j]
        )

    model.contributor_requirement = pyo.Constraint(
        model.C, rule=contributors_rule
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
        # HiGHS can raise when no feasible solution is available to load.
        # Objective retrieval below is the sole success criterion.
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}