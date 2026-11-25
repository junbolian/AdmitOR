import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    revenue = params["revenue"]
    demand = params["demand"]
    flight_capacity = params["flight_capacity"]

    num_packages = len(revenue)
    num_legs = len(flight_capacity)

    leg_packages = [
        [0, 1, 2, 3, 6, 7, 9],
        [0, 1, 4, 6],
        [1, 5, 8, 9],
        [0, 1, 4, 8],
        [1, 3, 4],
        [0, 2, 5],
        [2, 3, 4, 7, 8],
    ]

    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, num_packages - 1)
    model.L = pyo.RangeSet(0, num_legs - 1)

    model.x = pyo.Var(model.P, domain=pyo.NonNegativeIntegers)

    def demand_rule(m, i):
        return m.x[i] <= demand[i]
    model.demand_con = pyo.Constraint(model.P, rule=demand_rule)

    def capacity_rule(m, j):
        return sum(m.x[i] for i in leg_packages[j]) <= flight_capacity[j]
    model.capacity_con = pyo.Constraint(model.L, rule=capacity_rule)

    def obj_rule(m):
        return sum(revenue[i] * m.x[i] for i in m.P)
    model.profit = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.profit))
    return {"objective": obj_val, "status": "optimal"}