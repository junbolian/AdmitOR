# IR: {
#   "sets": {"packages": "0..21", "legs": "0..19", "packages_using_leg": {
#     "0": [1,2,3,5,7,8,9,12,13,14,16,19,21],
#     "1": [3,4,5,6,9,14,16,17,18,20],
#     "2": [0,2,3,4,5,6,8,9,11,12,13,14,15,18,19,20,21],
#     "3": [4,5,6,8,9,10,11,12,13,14,16,18,19,21],
#     "4": [3,4,8,9,10,12,15],
#     "5": [0,1,2,3,4,5,6,9,10,14,16,17,18,19,20,21],
#     "6": [0,5,7,8,10,11,14,17,18,20],
#     "7": [0,7,10,12,13,18,19,20,21],
#     "8": [3,7,8,9,10,13,15,17,19,20],
#     "9": [0,3,5,6,9,10,11,14,15,16],
#     "10": [0,1,5,6,9,11,12,19,20],
#     "11": [2,6,9,10,12,14,15,16,18,19],
#     "12": [0,1,2,3,5,8,9,10,12,15,17,18,19,21],
#     "13": [0,1,4,5,8,9,11,15,16,17,18],
#     "14": [5,6,8,11,12,14,15,16],
#     "15": [1,3,10,12,13,15,16,18],
#     "16": [1,4,5,6,7,8,11,12,15,18,20,21],
#     "17": [4,6,7,8,11,12,13,14,17,19,20,21],
#     "18": [4,8,10,11,12,16,20],
#     "19": [1,2,6,7,8,9,10,11,12,14,16,20,21]
#   }},
#   "params": {
#     "revenue": "real[packages], from params['revenue']",
#     "demand": "real[packages], from params['demand']",
#     "leg_capacity": "real[legs], from params['leg_capacity']"
#   },
#   "decision_variables": {"sales[p]": "nonnegative integer, p in packages"},
#   "constraints": [
#     "sales[p] <= demand[p] for each p in packages",
#     "sum(sales[p] for p in packages_using_leg[l]) <= leg_capacity[l] for each l in legs"
#   ],
#   "objective": "maximize sum(revenue[p] * sales[p] for p in packages)"
# }

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    packages_using_leg = {
        0: (1, 2, 3, 5, 7, 8, 9, 12, 13, 14, 16, 19, 21),
        1: (3, 4, 5, 6, 9, 14, 16, 17, 18, 20),
        2: (0, 2, 3, 4, 5, 6, 8, 9, 11, 12, 13, 14, 15, 18, 19, 20, 21),
        3: (4, 5, 6, 8, 9, 10, 11, 12, 13, 14, 16, 18, 19, 21),
        4: (3, 4, 8, 9, 10, 12, 15),
        5: (0, 1, 2, 3, 4, 5, 6, 9, 10, 14, 16, 17, 18, 19, 20, 21),
        6: (0, 5, 7, 8, 10, 11, 14, 17, 18, 20),
        7: (0, 7, 10, 12, 13, 18, 19, 20, 21),
        8: (3, 7, 8, 9, 10, 13, 15, 17, 19, 20),
        9: (0, 3, 5, 6, 9, 10, 11, 14, 15, 16),
        10: (0, 1, 5, 6, 9, 11, 12, 19, 20),
        11: (2, 6, 9, 10, 12, 14, 15, 16, 18, 19),
        12: (0, 1, 2, 3, 5, 8, 9, 10, 12, 15, 17, 18, 19, 21),
        13: (0, 1, 4, 5, 8, 9, 11, 15, 16, 17, 18),
        14: (5, 6, 8, 11, 12, 14, 15, 16),
        15: (1, 3, 10, 12, 13, 15, 16, 18),
        16: (1, 4, 5, 6, 7, 8, 11, 12, 15, 18, 20, 21),
        17: (4, 6, 7, 8, 11, 12, 13, 14, 17, 19, 20, 21),
        18: (4, 8, 10, 11, 12, 16, 20),
        19: (1, 2, 6, 7, 8, 9, 10, 11, 12, 14, 16, 20, 21),
    }

    model = pyo.ConcreteModel()
    model.packages = pyo.RangeSet(0, 21)
    model.legs = pyo.RangeSet(0, 19)

    model.revenue = pyo.Param(
        model.packages,
        initialize={p: params["revenue"][p] for p in model.packages},
        within=pyo.Reals,
    )
    model.demand = pyo.Param(
        model.packages,
        initialize={p: params["demand"][p] for p in model.packages},
        within=pyo.Reals,
    )
    model.leg_capacity = pyo.Param(
        model.legs,
        initialize={leg: params["leg_capacity"][leg] for leg in model.legs},
        within=pyo.Reals,
    )
    model.packages_using_leg = pyo.Set(
        model.legs,
        within=model.packages,
        initialize=packages_using_leg,
    )

    model.sales = pyo.Var(
        model.packages,
        domain=pyo.NonNegativeIntegers,
    )

    def demand_rule(instance, package):
        return instance.sales[package] <= instance.demand[package]

    model.demand_limits = pyo.Constraint(
        model.packages,
        rule=demand_rule,
    )

    def capacity_rule(instance, leg):
        return (
            sum(
                instance.sales[package]
                for package in instance.packages_using_leg[leg]
            )
            <= instance.leg_capacity[leg]
        )

    model.capacity_limits = pyo.Constraint(
        model.legs,
        rule=capacity_rule,
    )

    model.total_revenue = pyo.Objective(
        expr=sum(
            model.revenue[package] * model.sales[package]
            for package in model.packages
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_revenue))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}