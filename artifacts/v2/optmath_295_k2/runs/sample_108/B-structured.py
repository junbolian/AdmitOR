# IR: {"sets":{"P":[0,1,2],"C":[0,1,2,3]},"params":{"capacity[P]":"nonnegative real, params['capacity'][p]","demand[C]":"nonnegative real, params['demand'][c]","min_delivery[P]":"nonnegative real, params['min_delivery'][p]","cost[P,C]":"real, params['cost'][p][c]"},"variables":{"delivery[P,C]":"nonnegative continuous","participates[P,C]":"binary"},"constraints":["sum(delivery[p,c] for c in C) <= capacity[p], for p in P","sum(delivery[p,c] for p in P) >= demand[c], for c in C","sum(participates[p,c] for p in P) >= 2, for c in C","delivery[p,c] >= min_delivery[p]*participates[p,c], for (p,c) in P x C","delivery[p,c] <= capacity[p]*participates[p,c], for (p,c) in P x C"],"objective":"minimize sum(cost[p,c]*delivery[p,c] for (p,c) in P x C)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity = params["capacity"]
    demand = params["demand"]
    min_delivery = params["min_delivery"]
    cost = params["cost"]

    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, 2)
    model.C = pyo.RangeSet(0, 3)

    model.capacity = pyo.Param(
        model.P,
        initialize={p: capacity[p] for p in model.P},
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.C,
        initialize={c: demand[c] for c in model.C},
        within=pyo.NonNegativeReals,
    )
    model.min_delivery = pyo.Param(
        model.P,
        initialize={p: min_delivery[p] for p in model.P},
        within=pyo.NonNegativeReals,
    )
    model.cost = pyo.Param(
        model.P,
        model.C,
        initialize={
            (p, c): cost[p][c]
            for p in model.P
            for c in model.C
        },
        within=pyo.Reals,
    )

    model.delivery = pyo.Var(
        model.P, model.C, domain=pyo.NonNegativeReals
    )
    model.participates = pyo.Var(
        model.P, model.C, domain=pyo.Binary
    )

    def capacity_rule(instance, p):
        return (
            sum(instance.delivery[p, c] for c in instance.C)
            <= instance.capacity[p]
        )

    model.capacity_limit = pyo.Constraint(
        model.P, rule=capacity_rule
    )

    def demand_rule(instance, c):
        return (
            sum(instance.delivery[p, c] for p in instance.P)
            >= instance.demand[c]
        )

    model.demand_requirement = pyo.Constraint(
        model.C, rule=demand_rule
    )

    def contributor_rule(instance, c):
        return (
            sum(instance.participates[p, c] for p in instance.P)
            >= 2
        )

    model.contributor_requirement = pyo.Constraint(
        model.C, rule=contributor_rule
    )

    def minimum_delivery_rule(instance, p, c):
        return (
            instance.delivery[p, c]
            >= instance.min_delivery[p] * instance.participates[p, c]
        )

    model.minimum_delivery_link = pyo.Constraint(
        model.P, model.C, rule=minimum_delivery_rule
    )

    def participation_upper_rule(instance, p, c):
        return (
            instance.delivery[p, c]
            <= instance.capacity[p] * instance.participates[p, c]
        )

    model.participation_upper_link = pyo.Constraint(
        model.P, model.C, rule=participation_upper_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[p, c] * model.delivery[p, c]
            for p in model.P
            for c in model.C
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}