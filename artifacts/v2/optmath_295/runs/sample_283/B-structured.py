# IR: {"sets":{"P":"0..22","R":"0..14","S[r]":"ROUTE_PACKAGES[r] as defined below"},"params":{"revenue":"params['revenue'][p], p in P","demand_limit":"params['demand_limit'][p], p in P","route_capacity":"params['route_capacity'][r], r in R"},"variables":{"units[p]":"nonnegative integer, p in P"},"constraints":["units[p] <= demand_limit[p] for each p in P","sum(units[p] for p in S[r]) <= route_capacity[r] for each r in R"],"objective":"maximize sum(revenue[p] * units[p] for p in P)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


ROUTE_PACKAGES = {
    0: (
        0, 1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 15, 16, 17,
        18, 19, 20, 21,
    ),
    1: (
        1, 2, 4, 5, 6, 8, 9, 10, 11, 12, 14, 15, 16, 17, 18,
        19, 22,
    ),
    2: (
        2, 3, 4, 8, 9, 11, 12, 13, 15, 17, 18, 20, 21,
    ),
    3: (
        0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14,
        15, 16, 17, 19, 20, 21, 22,
    ),
    4: (
        1, 3, 4, 5, 7, 8, 9, 10, 13, 14, 15, 17, 18, 20, 21, 22,
    ),
    5: (
        0, 1, 2, 4, 5, 6, 8, 9, 10, 11, 12, 13, 16, 17, 18,
        20, 21, 22,
    ),
    6: (
        0, 1, 2, 3, 4, 5, 6, 8, 9, 13, 15, 16, 17, 18, 19,
        21, 22,
    ),
    7: (
        0, 1, 2, 5, 7, 8, 10, 12, 14, 16, 19, 20, 21, 22,
    ),
    8: (
        2, 3, 4, 5, 6, 7, 9, 10, 12, 13, 14, 15, 16, 17, 18,
        19, 20, 21, 22,
    ),
    9: (
        0, 1, 5, 6, 7, 8, 9, 10, 13, 14, 15, 17, 18, 19, 20,
    ),
    10: (
        0, 1, 2, 3, 4, 6, 8, 9, 10, 12, 13, 14, 15, 16, 17, 22,
    ),
    11: (
        1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15,
        16, 18, 19, 20, 21,
    ),
    12: (
        0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 14, 15,
        16, 17, 18, 19, 20, 21, 22,
    ),
    13: (
        0, 1, 2, 6, 7, 8, 10, 11, 13, 15, 16, 17, 18, 19, 20, 22,
    ),
    14: (
        0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14,
        15, 17, 18, 19, 20, 21, 22,
    ),
}


def solve(params):
    revenue = params["revenue"]
    demand_limit = params["demand_limit"]
    route_capacity = params["route_capacity"]

    model = pyo.ConcreteModel()
    model.packages = pyo.RangeSet(0, 22)
    model.routes = pyo.RangeSet(0, 14)

    model.revenue = pyo.Param(
        model.packages,
        initialize={p: revenue[p] for p in model.packages},
        within=pyo.Reals,
    )
    model.demand_limit = pyo.Param(
        model.packages,
        initialize={p: demand_limit[p] for p in model.packages},
        within=pyo.Reals,
    )
    model.route_capacity = pyo.Param(
        model.routes,
        initialize={r: route_capacity[r] for r in model.routes},
        within=pyo.Reals,
    )

    model.units = pyo.Var(
        model.packages,
        domain=pyo.NonNegativeIntegers,
    )

    def demand_rule(instance, p):
        return instance.units[p] <= instance.demand_limit[p]

    model.demand_constraints = pyo.Constraint(
        model.packages,
        rule=demand_rule,
    )

    def capacity_rule(instance, r):
        return (
            pyo.quicksum(instance.units[p] for p in ROUTE_PACKAGES[r])
            <= instance.route_capacity[r]
        )

    model.capacity_constraints = pyo.Constraint(
        model.routes,
        rule=capacity_rule,
    )

    model.total_revenue = pyo.Objective(
        expr=pyo.quicksum(
            model.revenue[p] * model.units[p] for p in model.packages
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_revenue))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}