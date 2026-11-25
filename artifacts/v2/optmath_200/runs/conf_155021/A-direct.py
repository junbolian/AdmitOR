import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

# Structural index sets (do not hardcode numeric params)
PACKAGES = list(range(24))
CAPACITY_CONSTRAINTS = list(range(15))

# Participation lists for each capacity constraint (structural, from the problem statement)
CAPACITY_PARTICIPATION = {
    0: [0, 1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 15, 16, 17, 18, 19, 21, 22, 23],
    1: [0, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13, 15, 17, 18, 19, 20, 21, 22],
    2: [0, 1, 2, 3, 4, 5, 6, 8, 9, 11, 13, 14, 15, 17, 18, 19, 20, 22, 23],
    3: [1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15, 16, 18, 19, 20, 21, 23],
    4: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23],
    5: [0, 1, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15, 17, 18, 19, 20, 22, 23],
    6: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23],
    7: [0, 2, 5, 6, 7, 8, 9, 11, 12, 13, 15, 17, 20, 21, 23],
    8: [1, 2, 3, 5, 7, 8, 9, 11, 12, 13, 14, 15, 17, 19, 20, 21, 23],
    9: [2, 3, 4, 5, 6, 9, 11, 12, 14, 15, 16, 18, 19, 20, 21, 23],
    10: [0, 2, 3, 4, 5, 6, 7, 9, 11, 12, 13, 14, 16, 17, 18, 19, 20, 21, 22],
    11: [0, 1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23],
    12: [0, 1, 3, 4, 6, 7, 8, 9, 10, 12, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23],
    13: [0, 1, 2, 3, 5, 6, 7, 8, 9, 10, 11, 12, 14, 15, 17, 18, 19, 20, 21, 22, 23],
    14: [0, 1, 8, 9, 10, 11, 13, 15, 16, 17, 18, 19, 20, 22, 23],
}


def solve(params):
    revenue = params["revenue"]
    demand_limit = params["demand_limit"]
    capacity_limit = params["capacity_limit"]

    model = pyo.ConcreteModel()

    model.PACKAGES = pyo.Set(initialize=PACKAGES, ordered=True)
    model.CAPS = pyo.Set(initialize=CAPACITY_CONSTRAINTS, ordered=True)

    model.units = pyo.Var(model.PACKAGES, domain=pyo.NonNegativeIntegers)

    def demand_rule(m, j):
        return m.units[j] <= demand_limit[j]

    model.demand_con = pyo.Constraint(model.PACKAGES, rule=demand_rule)

    def capacity_rule(m, c):
        return sum(m.units[j] for j in CAPACITY_PARTICIPATION[c]) <= capacity_limit[c]

    model.capacity_con = pyo.Constraint(model.CAPS, rule=capacity_rule)

    def obj_rule(m):
        return sum(revenue[j] * m.units[j] for j in m.PACKAGES)

    model.total_revenue = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_revenue))
    return {"objective": obj_val, "status": "optimal"}