import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    revenue = params["revenue"]
    demand_limit = params["demand_limit"]
    seat_capacity = params["seat_capacity"]

    packages = list(range(22))
    legs = list(range(20))

    leg_uses = {
        0: [1, 2, 3, 5, 7, 8, 9, 12, 13, 14, 16, 19, 21],
        1: [3, 4, 5, 6, 9, 14, 16, 17, 18, 20],
        2: [0, 2, 3, 4, 5, 6, 8, 9, 11, 12, 13, 14, 15, 18, 19, 20, 21],
        3: [4, 5, 6, 8, 9, 10, 11, 12, 13, 14, 16, 18, 19, 21],
        4: [3, 4, 8, 9, 10, 12, 15],
        5: [0, 1, 2, 3, 4, 5, 6, 9, 10, 14, 16, 17, 18, 19, 20, 21],
        6: [0, 5, 7, 8, 10, 11, 14, 17, 18, 20],
        7: [0, 7, 10, 12, 13, 18, 19, 20, 21],
        8: [3, 7, 8, 9, 10, 13, 15, 17, 19, 20],
        9: [0, 3, 5, 6, 9, 10, 11, 14, 15, 16],
        10: [0, 1, 5, 6, 9, 11, 12, 19, 20],
        11: [2, 6, 9, 10, 12, 14, 15, 16, 18, 19],
        12: [0, 1, 2, 3, 5, 8, 9, 10, 12, 15, 17, 18, 19, 21],
        13: [0, 1, 4, 5, 8, 9, 11, 15, 16, 17, 18],
        14: [5, 6, 8, 11, 12, 14, 15, 16],
        15: [1, 3, 10, 12, 13, 15, 16, 18],
        16: [1, 4, 5, 6, 7, 8, 11, 12, 15, 18, 20, 21],
        17: [4, 6, 7, 8, 11, 12, 13, 14, 17, 19, 20, 21],
        18: [4, 8, 10, 11, 12, 16, 20],
        19: [1, 2, 6, 7, 8, 9, 10, 11, 12, 14, 16, 20, 21],
    }

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=packages)
    model.L = pyo.Set(initialize=legs)

    model.x = pyo.Var(model.P, within=pyo.NonNegativeIntegers)

    def obj_rule(m):
        return sum(revenue[i] * m.x[i] for i in m.P)

    model.total_revenue = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def demand_rule(m, i):
        return m.x[i] <= demand_limit[i]

    model.demand_con = pyo.Constraint(model.P, rule=demand_rule)

    def cap_rule(m, j):
        return sum(m.x[i] for i in leg_uses[j]) <= seat_capacity[j]

    model.seat_con = pyo.Constraint(model.L, rule=cap_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_revenue))

    return {"objective": obj_val, "status": "optimal"}