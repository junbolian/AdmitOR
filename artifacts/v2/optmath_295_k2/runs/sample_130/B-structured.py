# IR: {"sets":{"P":[0,1,2,3],"C":[0,1,2,3,4]},"params":{"capacity":"capacity[p] >= 0","demand":"demand[c] >= 0","min_delivery":"min_delivery[p] > 0","cost":"cost[p][c] real"},"variables":{"delivery[p,c]":"NonNegativeReals","contributes[p,c]":"Binary"},"constraints":["sum(c in C, delivery[p,c]) <= capacity[p] for p in P","sum(p in P, delivery[p,c]) >= demand[c] for c in C","sum(p in P, contributes[p,c]) >= 2 for c in C","delivery[p,c] >= min_delivery[p]*contributes[p,c] for p in P,c in C","delivery[p,c] <= capacity[p]*contributes[p,c] for p in P,c in C"],"objective":"minimize sum(p in P,c in C, cost[p][c]*delivery[p,c])"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, 3)
    model.C = pyo.RangeSet(0, 4)

    model.capacity = pyo.Param(
        model.P,
        initialize={p: params["capacity"][p] for p in model.P},
        within=pyo.NonNegativeReals,
    )
    model.demand = pyo.Param(
        model.C,
        initialize={c: params["demand"][c] for c in model.C},
        within=pyo.NonNegativeReals,
    )
    model.min_delivery = pyo.Param(
        model.P,
        initialize={p: params["min_delivery"][p] for p in model.P},
        within=pyo.PositiveReals,
    )
    model.cost = pyo.Param(
        model.P,
        model.C,
        initialize={
            (p, c): params["cost"][p][c]
            for p in model.P
            for c in model.C
        },
        within=pyo.Reals,
    )

    model.delivery = pyo.Var(
        model.P, model.C, domain=pyo.NonNegativeReals
    )
    model.contributes = pyo.Var(model.P, model.C, domain=pyo.Binary)

    def capacity_rule(model, p):
        return (
            sum(model.delivery[p, c] for c in model.C)
            <= model.capacity[p]
        )

    model.capacity_constraints = pyo.Constraint(
        model.P, rule=capacity_rule
    )

    def demand_rule(model, c):
        return (
            sum(model.delivery[p, c] for p in model.P)
            >= model.demand[c]
        )

    model.demand_constraints = pyo.Constraint(
        model.C, rule=demand_rule
    )

    def contributors_rule(model, c):
        return sum(model.contributes[p, c] for p in model.P) >= 2

    model.contributor_constraints = pyo.Constraint(
        model.C, rule=contributors_rule
    )

    def minimum_delivery_rule(model, p, c):
        return (
            model.delivery[p, c]
            >= model.min_delivery[p] * model.contributes[p, c]
        )

    model.minimum_delivery_constraints = pyo.Constraint(
        model.P, model.C, rule=minimum_delivery_rule
    )

    def delivery_link_rule(model, p, c):
        return (
            model.delivery[p, c]
            <= model.capacity[p] * model.contributes[p, c]
        )

    model.delivery_link_constraints = pyo.Constraint(
        model.P, model.C, rule=delivery_link_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[p, c] * model.delivery[p, c]
            for p in model.P
            for c in model.C
        ),
        sense=pyo.minimize,
    )

    # HiGHS can raise RuntimeError when no feasible solution can be loaded.
    solver_failed = False
    try:
        Highs().solve(model)
    except RuntimeError:
        solver_failed = True

    # Success depends exclusively on retrieving the objective value.
    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {
            "objective": None,
            "status": "solver_failed" if solver_failed else "no_objective",
        }

    return {"objective": obj_val, "status": "optimal"}