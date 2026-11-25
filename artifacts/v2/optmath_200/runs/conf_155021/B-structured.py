# IR: {"sets":{"packages":"0..23","capacities":"0..14","members":{"0":[0,1,2,3,5,6,7,8,9,10,11,12,13,15,16,17,18,19,21,22,23],"1":[0,2,3,4,5,6,7,8,9,11,12,13,15,17,18,19,20,21,22],"2":[0,1,2,3,4,5,6,8,9,11,13,14,15,17,18,19,20,22,23],"3":[1,2,3,4,5,6,7,9,10,11,12,13,14,15,16,18,19,20,21,23],"4":[0,1,2,3,4,5,6,7,8,9,10,13,14,15,16,17,18,19,20,21,22,23],"5":[0,1,3,4,5,6,7,9,10,11,12,13,14,15,17,18,19,20,22,23],"6":[1,2,3,4,5,6,7,8,9,10,11,12,14,15,16,17,18,19,20,21,22,23],"7":[0,2,5,6,7,8,9,11,12,13,15,17,20,21,23],"8":[1,2,3,5,7,8,9,11,12,13,14,15,17,19,20,21,23],"9":[2,3,4,5,6,9,11,12,14,15,16,18,19,20,21,23],"10":[0,2,3,4,5,6,7,9,11,12,13,14,16,17,18,19,20,21,22],"11":[0,1,2,3,5,6,7,8,9,10,11,13,14,15,16,17,18,19,20,21,22,23],"12":[0,1,3,4,6,7,8,9,10,12,14,15,16,17,18,19,20,21,22,23],"13":[0,1,2,3,5,6,7,8,9,10,11,12,14,15,17,18,19,20,21,22,23],"14":[0,1,8,9,10,11,13,15,16,17,18,19,20,22,23]}},"params":{"revenue":"real[packages], from params['revenue']","demand_limit":"real[packages], from params['demand_limit']","capacity_limit":"real[capacities], from params['capacity_limit']"},"variables":{"units":"nonnegative integer[packages]"},"constraints":["demand[j]: units[j] <= demand_limit[j] for each package j","capacity[k]: sum(units[j] for j in members[k]) <= capacity_limit[k] for each capacity k"],"objective":"maximize sum(revenue[j] * units[j] for j in packages)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    members = {
        0: (0, 1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 15, 16, 17,
            18, 19, 21, 22, 23),
        1: (0, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13, 15, 17, 18, 19,
            20, 21, 22),
        2: (0, 1, 2, 3, 4, 5, 6, 8, 9, 11, 13, 14, 15, 17, 18, 19,
            20, 22, 23),
        3: (1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15, 16, 18,
            19, 20, 21, 23),
        4: (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 13, 14, 15, 16, 17,
            18, 19, 20, 21, 22, 23),
        5: (0, 1, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15, 17, 18,
            19, 20, 22, 23),
        6: (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 15, 16, 17,
            18, 19, 20, 21, 22, 23),
        7: (0, 2, 5, 6, 7, 8, 9, 11, 12, 13, 15, 17, 20, 21, 23),
        8: (1, 2, 3, 5, 7, 8, 9, 11, 12, 13, 14, 15, 17, 19, 20,
            21, 23),
        9: (2, 3, 4, 5, 6, 9, 11, 12, 14, 15, 16, 18, 19, 20, 21, 23),
        10: (0, 2, 3, 4, 5, 6, 7, 9, 11, 12, 13, 14, 16, 17, 18, 19,
             20, 21, 22),
        11: (0, 1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 13, 14, 15, 16, 17,
             18, 19, 20, 21, 22, 23),
        12: (0, 1, 3, 4, 6, 7, 8, 9, 10, 12, 14, 15, 16, 17, 18, 19,
             20, 21, 22, 23),
        13: (0, 1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 14, 15, 17, 18,
             19, 20, 21, 22, 23),
        14: (0, 1, 8, 9, 10, 11, 13, 15, 16, 17, 18, 19, 20, 22, 23),
    }

    revenue = params["revenue"]
    demand_limit = params["demand_limit"]
    capacity_limit = params["capacity_limit"]

    model = pyo.ConcreteModel()
    model.packages = pyo.RangeSet(0, 23)
    model.capacities = pyo.RangeSet(0, 14)

    model.revenue = pyo.Param(
        model.packages,
        initialize={j: revenue[j] for j in range(24)},
        within=pyo.Reals,
    )
    model.demand_limit = pyo.Param(
        model.packages,
        initialize={j: demand_limit[j] for j in range(24)},
        within=pyo.Reals,
    )
    model.capacity_limit = pyo.Param(
        model.capacities,
        initialize={k: capacity_limit[k] for k in range(15)},
        within=pyo.Reals,
    )

    model.units = pyo.Var(model.packages, domain=pyo.NonNegativeIntegers)

    def demand_rule(problem, j):
        return problem.units[j] <= problem.demand_limit[j]

    model.demand_constraints = pyo.Constraint(
        model.packages, rule=demand_rule
    )

    def capacity_rule(problem, k):
        return (
            sum(problem.units[j] for j in members[k])
            <= problem.capacity_limit[k]
        )

    model.capacity_constraints = pyo.Constraint(
        model.capacities, rule=capacity_rule
    )

    model.total_revenue = pyo.Objective(
        expr=sum(
            model.revenue[j] * model.units[j]
            for j in model.packages
        ),
        sense=pyo.maximize,
    )

    failure_reason = "objective_unavailable"
    try:
        Highs().solve(model)
    except RuntimeError:
        # An infeasible solve can raise when HiGHS attempts to load a solution.
        # Objective retrieval below remains the sole success criterion.
        failure_reason = "solve_failed"

    try:
        obj_val = float(pyo.value(model.total_revenue))
    except (ValueError, TypeError):
        return {"objective": None, "status": failure_reason}

    return {"objective": obj_val, "status": "optimal"}