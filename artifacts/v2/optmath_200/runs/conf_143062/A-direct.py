import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    revenue = params["revenue"]
    demand = params["demand"]
    flight_capacity = params["flight_capacity"]

    num_packages = len(revenue)
    num_legs = len(flight_capacity)

    packages_for_leg = [
        [0, 2, 4, 7, 11, 12, 16, 17, 19],
        [0, 1, 7, 9, 10, 11, 15, 20],
        [0, 1, 3, 4, 7, 11, 13, 15, 17, 19],
        [6, 7, 9, 15, 16, 17, 18, 19],
        [2, 3, 4, 5, 7, 11, 12, 13, 15, 16, 17, 19, 20],
        [0, 1, 3, 4, 5, 6, 8, 9, 10, 12, 14, 18],
        [1, 4, 5, 7, 8, 10, 13, 14, 16, 17, 18, 19, 20],
        [0, 1, 2, 4, 8, 9, 11, 13, 14, 15, 16, 17, 18, 19, 20],
        [0, 5, 9, 10, 12, 14, 15, 16, 20],
        [2, 4, 5, 6, 7, 8, 9, 10, 11, 16, 18, 19],
        [2, 6, 12, 15, 17, 18],
        [1, 10, 13, 14, 15, 19],
        [1, 2, 4, 5, 6, 8, 9, 11, 13, 14, 17, 18, 20],
        [0, 1, 4, 5, 7, 8, 9, 10, 14, 16, 17, 19],
        [0, 1, 2, 3, 7, 9, 11, 14, 16, 18, 19],
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 13, 15, 19],
        [2, 6, 8, 9, 12, 13, 16, 17, 19, 20],
        [1, 2, 3, 6, 7, 10, 11, 14, 18],
    ]

    model = pyo.ConcreteModel()

    model.packages = pyo.RangeSet(0, num_packages - 1)
    model.legs = pyo.RangeSet(0, num_legs - 1)

    model.Sell = pyo.Var(model.packages, domain=pyo.NonNegativeIntegers)

    def objective_rule(m):
        return sum(revenue[p] * m.Sell[p] for p in m.packages)

    model.total_revenue = pyo.Objective(rule=objective_rule, sense=pyo.maximize)

    def demand_rule(m, p):
        return m.Sell[p] <= demand[p]

    model.demand_limit = pyo.Constraint(model.packages, rule=demand_rule)

    def capacity_rule(m, l):
        return sum(m.Sell[p] for p in packages_for_leg[l]) <= flight_capacity[l]

    model.capacity_limit = pyo.Constraint(model.legs, rule=capacity_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_revenue))
    return {"objective": obj_val, "status": "optimal"}