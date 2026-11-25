# IR (JSON):
# {
#   "sets": {
#     "P": "0..24",
#     "R": "0..14",
#     "U": {
#       "0": [2,4,5,7,8,9,10,11,12,13,14,15,17,18,19,20,21,22,24],
#       "1": [0,1,2,4,6,7,8,9,10,11,12,14,16,17,19,20,21,22,23,24],
#       "2": [0,1,5,6,8,9,13,14,15,16,17,19,23],
#       "3": [0,2,3,4,5,6,8,9,10,11,12,13,15,17,18,19,20,21,22,23,24],
#       "4": [1,2,3,5,7,8,9,10,11,12,13,14,15,17,19,20,22,23],
#       "5": [1,2,6,9,10,12,14,15,16,17,18,19,21,22,23],
#       "6": [0,1,2,3,4,5,7,9,10,11,12,14,15,16,17,19,20,22,23],
#       "7": [0,1,2,5,6,8,9,11,12,13,14,15,16,17,18,20,21,22,24],
#       "8": [1,2,4,5,6,8,10,12,13,14,16,17,18,19,20,22,23],
#       "9": [0,1,2,3,4,5,6,7,8,9,11,12,13,14,15,16,18,20,21,22],
#       "10": [0,1,2,3,4,5,7,8,9,11,14,17,18,20,21,22,23,24],
#       "11": [0,4,6,7,9,10,13,14,15,18,19,20,21,22,24],
#       "12": [1,2,3,4,6,7,8,9,11,13,14,15,16,17,18,19,20,21,23,24],
#       "13": [0,1,2,3,4,6,7,9,10,11,12,13,14,15,16,17,18,20,21,22,23,24],
#       "14": [0,1,2,3,4,5,6,9,10,13,14,15,17,18,21,23]
#     }
#   },
#   "params": {
#     "revenue[p]": "params['revenue'][p], real",
#     "demand[p]": "params['demand'][p], real",
#     "capacity[r]": "params['capacity'][r], real"
#   },
#   "decision_variables": {"x[p]": "nonnegative real, p in P"},
#   "constraints": [
#     "x[p] <= demand[p] for each p in P",
#     "sum(x[p] for p in U[r]) <= capacity[r] for each r in R"
#   ],
#   "objective": "maximize sum(revenue[p] * x[p] for p in P)"
# }

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    revenue = params["revenue"]
    demand = params["demand"]
    capacity = params["capacity"]

    resource_packages = {
        0: (2, 4, 5, 7, 8, 9, 10, 11, 12, 13, 14, 15, 17, 18,
            19, 20, 21, 22, 24),
        1: (0, 1, 2, 4, 6, 7, 8, 9, 10, 11, 12, 14, 16, 17, 19,
            20, 21, 22, 23, 24),
        2: (0, 1, 5, 6, 8, 9, 13, 14, 15, 16, 17, 19, 23),
        3: (0, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12, 13, 15, 17, 18,
            19, 20, 21, 22, 23, 24),
        4: (1, 2, 3, 5, 7, 8, 9, 10, 11, 12, 13, 14, 15, 17, 19,
            20, 22, 23),
        5: (1, 2, 6, 9, 10, 12, 14, 15, 16, 17, 18, 19, 21, 22, 23),
        6: (0, 1, 2, 3, 4, 5, 7, 9, 10, 11, 12, 14, 15, 16, 17,
            19, 20, 22, 23),
        7: (0, 1, 2, 5, 6, 8, 9, 11, 12, 13, 14, 15, 16, 17, 18,
            20, 21, 22, 24),
        8: (1, 2, 4, 5, 6, 8, 10, 12, 13, 14, 16, 17, 18, 19,
            20, 22, 23),
        9: (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13, 14, 15,
            16, 18, 20, 21, 22),
        10: (0, 1, 2, 3, 4, 5, 7, 8, 9, 11, 14, 17, 18, 20,
             21, 22, 23, 24),
        11: (0, 4, 6, 7, 9, 10, 13, 14, 15, 18, 19, 20, 21, 22, 24),
        12: (1, 2, 3, 4, 6, 7, 8, 9, 11, 13, 14, 15, 16, 17,
             18, 19, 20, 21, 23, 24),
        13: (0, 1, 2, 3, 4, 6, 7, 9, 10, 11, 12, 13, 14, 15,
             16, 17, 18, 20, 21, 22, 23, 24),
        14: (0, 1, 2, 3, 4, 5, 6, 9, 10, 13, 14, 15, 17, 18, 21, 23),
    }

    model = pyo.ConcreteModel()
    model.packages = pyo.RangeSet(0, 24)
    model.resources = pyo.RangeSet(0, 14)

    model.resource_packages = pyo.Set(
        model.resources,
        within=model.packages,
        initialize=resource_packages,
    )

    model.revenue = pyo.Param(
        model.packages,
        initialize=lambda mdl, package: revenue[package],
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        model.packages,
        initialize=lambda mdl, package: demand[package],
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.resources,
        initialize=lambda mdl, resource: capacity[resource],
        within=pyo.Reals,
    )

    model.units_sold = pyo.Var(
        model.packages,
        domain=pyo.NonNegativeReals,
    )

    model.demand_limits = pyo.Constraint(
        model.packages,
        rule=lambda mdl, package: (
            mdl.units_sold[package] <= mdl.demand[package]
        ),
    )

    def resource_limit_rule(mdl, resource):
        return (
            sum(
                mdl.units_sold[package]
                for package in mdl.resource_packages[resource]
            )
            <= mdl.capacity[resource]
        )

    model.resource_limits = pyo.Constraint(
        model.resources,
        rule=resource_limit_rule,
    )

    model.total_revenue = pyo.Objective(
        expr=sum(
            model.revenue[package] * model.units_sold[package]
            for package in model.packages
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_revenue))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}