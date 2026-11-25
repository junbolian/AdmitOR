# IR: {"sets":{"P":[0,1],"L":[0,1]},"params":{"cost[p]":["cost_plane0","cost_plane1"],"capacity[p]":["capacity_plane0","capacity_plane1"],"fleet[p]":["fleet_plane0","fleet_plane1"],"max_trips[p]":["max_trips_plane0","max_trips_plane1"],"demand":"demand_0to1"},"variables":{"initial[p,l]":"nonnegative integer","idle[p,l]":"nonnegative integer","forward[p]":"nonnegative integer","reverse[p]":"nonnegative integer"},"constraints":["sum(p,capacity[p]*forward[p]) >= demand","initial[p,0] = idle[p,0] + forward[p] for each p","initial[p,1] = idle[p,1] + reverse[p] for each p","sum(l,initial[p,l]) <= fleet[p] for each p","forward[p] <= max_trips[p] for each p","reverse[p] = 0 for each p"],"objective":"minimize sum(p,cost[p]*(forward[p]+reverse[p]))"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=[0, 1])
    model.L = pyo.Set(initialize=[0, 1])

    model.cost = pyo.Param(
        model.P,
        initialize={
            0: params["cost_plane0"],
            1: params["cost_plane1"],
        },
    )
    model.capacity = pyo.Param(
        model.P,
        initialize={
            0: params["capacity_plane0"],
            1: params["capacity_plane1"],
        },
    )
    model.fleet = pyo.Param(
        model.P,
        initialize={
            0: params["fleet_plane0"],
            1: params["fleet_plane1"],
        },
    )
    model.max_trips = pyo.Param(
        model.P,
        initialize={
            0: params["max_trips_plane0"],
            1: params["max_trips_plane1"],
        },
    )
    model.demand = pyo.Param(initialize=params["demand_0to1"])

    model.initial = pyo.Var(model.P, model.L, domain=pyo.NonNegativeIntegers)
    model.idle = pyo.Var(model.P, model.L, domain=pyo.NonNegativeIntegers)
    model.forward = pyo.Var(model.P, domain=pyo.NonNegativeIntegers)
    model.reverse = pyo.Var(model.P, domain=pyo.NonNegativeIntegers)

    model.demand_constraint = pyo.Constraint(
        expr=sum(
            model.capacity[plane] * model.forward[plane]
            for plane in model.P
        ) >= model.demand
    )

    def origin_balance_rule(model, plane):
        return (
            model.initial[plane, 0]
            == model.idle[plane, 0] + model.forward[plane]
        )

    model.origin_balance = pyo.Constraint(model.P, rule=origin_balance_rule)

    def destination_balance_rule(model, plane):
        return (
            model.initial[plane, 1]
            == model.idle[plane, 1] + model.reverse[plane]
        )

    model.destination_balance = pyo.Constraint(
        model.P, rule=destination_balance_rule
    )

    def fleet_limit_rule(model, plane):
        return (
            sum(model.initial[plane, location] for location in model.L)
            <= model.fleet[plane]
        )

    model.fleet_limit = pyo.Constraint(model.P, rule=fleet_limit_rule)

    def forward_limit_rule(model, plane):
        return model.forward[plane] <= model.max_trips[plane]

    model.forward_limit = pyo.Constraint(model.P, rule=forward_limit_rule)

    def reverse_limit_rule(model, plane):
        return model.reverse[plane] == 0

    model.reverse_limit = pyo.Constraint(model.P, rule=reverse_limit_rule)

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[plane]
            * (model.forward[plane] + model.reverse[plane])
            for plane in model.P
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}