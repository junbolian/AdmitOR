# IR: {"sets":{"P":"0..5","C":"0..5"},"params":{"cost":"real[P,C]","capacity":"nonnegative[P]","demand":"nonnegative[C]","min_contributors":"nonnegative_integer[C]","min_delivery":"nonnegative[P]"},"variables":{"delivery[P,C]":"nonnegative_real","selected[P,C]":"binary"},"constraints":["sum(delivery[i,j] for j in C) <= capacity[i] for i in P","sum(delivery[i,j] for i in P) >= demand[j] for j in C","sum(selected[i,j] for i in P) >= min_contributors[j] for j in C","delivery[i,j] >= min_delivery[i]*selected[i,j] for i in P,j in C","delivery[i,j] <= capacity[i]*selected[i,j] for i in P,j in C"],"objective":"minimize sum(cost[i,j]*delivery[i,j] for i in P,j in C)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["cost"]
    capacity = params["capacity"]
    demand = params["demand"]
    min_contributors = params["min_contributors"]
    min_delivery = params["min_delivery"]

    model = pyo.ConcreteModel()
    model.P = pyo.RangeSet(0, 5)
    model.C = pyo.RangeSet(0, 5)

    model.unit_cost = pyo.Param(
        model.P,
        model.C,
        initialize=lambda mdl, i, j: cost[i][j],
        within=pyo.Reals,
    )
    model.producer_capacity = pyo.Param(
        model.P,
        initialize=lambda mdl, i: capacity[i],
        within=pyo.NonNegativeReals,
    )
    model.contract_demand = pyo.Param(
        model.C,
        initialize=lambda mdl, j: demand[j],
        within=pyo.NonNegativeReals,
    )
    model.required_contributors = pyo.Param(
        model.C,
        initialize=lambda mdl, j: min_contributors[j],
        within=pyo.NonNegativeIntegers,
    )
    model.minimum_delivery = pyo.Param(
        model.P,
        initialize=lambda mdl, i: min_delivery[i],
        within=pyo.NonNegativeReals,
    )

    model.delivery = pyo.Var(
        model.P, model.C, domain=pyo.NonNegativeReals
    )
    model.selected = pyo.Var(model.P, model.C, domain=pyo.Binary)

    def capacity_rule(mdl, i):
        return (
            sum(mdl.delivery[i, j] for j in mdl.C)
            <= mdl.producer_capacity[i]
        )

    def demand_rule(mdl, j):
        return (
            sum(mdl.delivery[i, j] for i in mdl.P)
            >= mdl.contract_demand[j]
        )

    def contributors_rule(mdl, j):
        return (
            sum(mdl.selected[i, j] for i in mdl.P)
            >= mdl.required_contributors[j]
        )

    def minimum_delivery_rule(mdl, i, j):
        return (
            mdl.delivery[i, j]
            >= mdl.minimum_delivery[i] * mdl.selected[i, j]
        )

    def selection_link_rule(mdl, i, j):
        return (
            mdl.delivery[i, j]
            <= mdl.producer_capacity[i] * mdl.selected[i, j]
        )

    model.capacity_limits = pyo.Constraint(model.P, rule=capacity_rule)
    model.demand_requirements = pyo.Constraint(model.C, rule=demand_rule)
    model.contributor_requirements = pyo.Constraint(
        model.C, rule=contributors_rule
    )
    model.delivery_minimums = pyo.Constraint(
        model.P, model.C, rule=minimum_delivery_rule
    )
    model.selection_links = pyo.Constraint(
        model.P, model.C, rule=selection_link_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.unit_cost[i, j] * model.delivery[i, j]
            for i in model.P
            for j in model.C
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}