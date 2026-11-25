import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    revenue = params["revenue"]
    demand = params["demand"]
    capacity = params["capacity"]

    packages = list(range(25))
    resources = list(range(15))

    resource_packages = {
        0: [2, 4, 5, 7, 8, 9, 10, 11, 12, 13, 14, 15, 17, 18, 19, 20, 21, 22, 24],
        1: [0, 1, 2, 4, 6, 7, 8, 9, 10, 11, 12, 14, 16, 17, 19, 20, 21, 22, 23, 24],
        2: [0, 1, 5, 6, 8, 9, 13, 14, 15, 16, 17, 19, 23],
        3: [0, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12, 13, 15, 17, 18, 19, 20, 21, 22, 23, 24],
        4: [1, 2, 3, 5, 7, 8, 9, 10, 11, 12, 13, 14, 15, 17, 19, 20, 22, 23],
        5: [1, 2, 6, 9, 10, 12, 14, 15, 16, 17, 18, 19, 21, 22, 23],
        6: [0, 1, 2, 3, 4, 5, 7, 9, 10, 11, 12, 14, 15, 16, 17, 19, 20, 22, 23],
        7: [0, 1, 2, 5, 6, 8, 9, 11, 12, 13, 14, 15, 16, 17, 18, 20, 21, 22, 24],
        8: [1, 2, 4, 5, 6, 8, 10, 12, 13, 14, 16, 17, 18, 19, 20, 22, 23],
        9: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13, 14, 15, 16, 18, 20, 21, 22],
        10: [0, 1, 2, 3, 4, 5, 7, 8, 9, 11, 14, 17, 18, 20, 21, 22, 23, 24],
        11: [0, 4, 6, 7, 9, 10, 13, 14, 15, 18, 19, 20, 21, 22, 24],
        12: [1, 2, 3, 4, 6, 7, 8, 9, 11, 13, 14, 15, 16, 17, 18, 19, 20, 21, 23, 24],
        13: [0, 1, 2, 3, 4, 6, 7, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 20, 21, 22, 23, 24],
        14: [0, 1, 2, 3, 4, 5, 6, 9, 10, 13, 14, 15, 17, 18, 21, 23],
    }

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=packages)
    model.R = pyo.Set(initialize=resources)

    model.x = pyo.Var(model.P, within=pyo.NonNegativeReals, bounds=(0, None))

    def demand_rule(mdl, i):
        return mdl.x[i] <= demand[i]

    model.demand_con = pyo.Constraint(model.P, rule=demand_rule)

    def cap_rule(mdl, r):
        return sum(mdl.x[p] for p in resource_packages[r]) <= capacity[r]

    model.cap_con = pyo.Constraint(model.R, rule=cap_rule)

    def obj_rule(mdl):
        return sum(revenue[i] * mdl.x[i] for i in mdl.P)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}