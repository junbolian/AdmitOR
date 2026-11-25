# IR: {"sets":{"P":"0..24","R":"0..14","U[r]":"package indices in resource_packages[r] below"},"params":{"revenue":"real[P], from params['revenue']","demand":"real[P], from params['demand']","capacity":"real[R], from params['capacity']"},"variables":{"units[p]":"nonnegative continuous, p in P"},"constraints":["units[p] <= demand[p], for each p in P","sum(units[p] for p in U[r]) <= capacity[r], for each r in R"],"objective":"maximize sum(revenue[p] * units[p] for p in P)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    revenue = params["revenue"]
    demand = params["demand"]
    capacity = params["capacity"]

    resource_packages = {
        0: (2, 4, 5, 7, 8, 9, 10, 11, 12, 13, 14, 15, 17, 18, 19, 20, 21, 22, 24),
        1: (0, 1, 2, 4, 6, 7, 8, 9, 10, 11, 12, 14, 16, 17, 19, 20, 21, 22, 23, 24),
        2: (0, 1, 5, 6, 8, 9, 13, 14, 15, 16, 17, 19, 23),
        3: (0, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12, 13, 15, 17, 18, 19, 20, 21, 22, 23, 24),
        4: (1, 2, 3, 5, 7, 8, 9, 10, 11, 12, 13, 14, 15, 17, 19, 20, 22, 23),
        5: (1, 2, 6, 9, 10, 12, 14, 15, 16, 17, 18, 19, 21, 22, 23),
        6: (0, 1, 2, 3, 4, 5, 7, 9, 10, 11, 12, 14, 15, 16, 17, 19, 20, 22, 23),
        7: (0, 1, 2, 5, 6, 8, 9, 11, 12, 13, 14, 15, 16, 17, 18, 20, 21, 22, 24),
        8: (1, 2, 4, 5, 6, 8, 10, 12, 13, 14, 16, 17, 18, 19, 20, 22, 23),
        9: (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13, 14, 15, 16, 18, 20, 21, 22),
        10: (0, 1, 2, 3, 4, 5, 7, 8, 9, 11, 14, 17, 18, 20, 21, 22, 23, 24),
        11: (0, 4, 6, 7, 9, 10, 13, 14, 15, 18, 19, 20, 21, 22, 24),
        12: (1, 2, 3, 4, 6, 7, 8, 9, 11, 13, 14, 15, 16, 17, 18, 19, 20, 21, 23, 24),
        13: (0, 1, 2, 3, 4, 6, 7, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 20, 21, 22, 23, 24),
        14: (0, 1, 2, 3, 4, 5, 6, 9, 10, 13, 14, 15, 17, 18, 21, 23),
    }

    model = pyo.ConcreteModel()
    model.packages = pyo.RangeSet(0, 24)
    model.resources = pyo.RangeSet(0, 14)

    model.revenue = pyo.Param(
        model.packages,
        initialize={p: revenue[p] for p in model.packages},
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        model.packages,
        initialize={p: demand[p] for p in model.packages},
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.resources,
        initialize={r: capacity[r] for r in model.resources},
        within=pyo.Reals,
    )

    model.units = pyo.Var(model.packages, domain=pyo.NonNegativeReals)

    def demand_rule(model, p):
        return model.units[p] <= model.demand[p]

    model.demand_limits = pyo.Constraint(model.packages, rule=demand_rule)

    def capacity_rule(model, r):
        return (
            sum(model.units[p] for p in resource_packages[r])
            <= model.capacity[r]
        )

    model.resource_limits = pyo.Constraint(model.resources, rule=capacity_rule)

    model.total_revenue = pyo.Objective(
        expr=sum(
            model.revenue[p] * model.units[p]
            for p in model.packages
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_revenue))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}