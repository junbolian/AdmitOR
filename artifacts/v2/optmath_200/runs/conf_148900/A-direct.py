import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    revenue = params["revenue"]
    demand = params["demand"]
    capacity = params["capacity"]

    num_packages = len(revenue)
    num_legs = len(capacity)

    leg_packages = [
        [0, 8, 10],
        [1, 2, 4, 5, 6, 8, 9],
        [2, 3, 5, 6, 7, 8],
        [2, 6, 7, 8, 10],
        [1, 2, 9, 10],
        [2, 4, 5, 6, 8, 9],
        [0, 1, 3, 4, 5, 7, 8, 9],
    ]

    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, num_packages - 1)
    model.L = pyo.RangeSet(0, num_legs - 1)

    model.x = pyo.Var(model.P, domain=pyo.NonNegativeIntegers)

    def demand_rule(m, i):
        return m.x[i] <= demand[i]

    model.demand_con = pyo.Constraint(model.P, rule=demand_rule)

    def capacity_rule(m, j):
        return sum(m.x[i] for i in leg_packages[j]) <= capacity[j]

    model.capacity_con = pyo.Constraint(model.L, rule=capacity_rule)

    def obj_rule(m):
        return sum(revenue[i] * m.x[i] for i in m.P)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}