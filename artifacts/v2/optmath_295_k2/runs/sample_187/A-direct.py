import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

# Resource-to-package incidence structure (0-based package indices).
RESOURCE_PACKAGES = {
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


def solve(params):
    revenue = params["revenue"]
    demand = params["demand"]
    capacity = params["capacity"]

    n_pkg = len(revenue)
    packages = list(range(n_pkg))
    resources = sorted(RESOURCE_PACKAGES.keys())

    model = pyo.ConcreteModel()

    model.x = pyo.Var(packages, domain=pyo.NonNegativeReals)

    def demand_rule(md, i):
        return md.x[i] <= demand[i]
    model.demand_con = pyo.Constraint(packages, rule=demand_rule)

    def capacity_rule(md, r):
        return sum(md.x[i] for i in RESOURCE_PACKAGES[r]) <= capacity[r]
    model.capacity_con = pyo.Constraint(resources, rule=capacity_rule)

    def obj_rule(md):
        return sum(revenue[i] * md.x[i] for i in packages)
    model.total_revenue = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_revenue))
    return {"objective": obj_val, "status": "optimal"}