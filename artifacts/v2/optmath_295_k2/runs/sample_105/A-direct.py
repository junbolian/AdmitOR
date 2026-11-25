import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    revenue = params["revenue"]
    demand = params["demand"]
    leg_capacity = params["leg_capacity"]

    n_packages = len(revenue)
    n_legs = len(leg_capacity)

    # Leg membership: which packages consume seats on each leg
    leg_packages = [
        [1, 2, 3, 5, 7, 8, 9, 12, 13, 14, 16, 19, 21],
        [3, 4, 5, 6, 9, 14, 16, 17, 18, 20],
        [0, 2, 3, 4, 5, 6, 8, 9, 11, 12, 13, 14, 15, 18, 19, 20, 21],
        [4, 5, 6, 8, 9, 10, 11, 12, 13, 14, 16, 18, 19, 21],
        [3, 4, 8, 9, 10, 12, 15],
        [0, 1, 2, 3, 4, 5, 6, 9, 10, 14, 16, 17, 18, 19, 20, 21],
        [0, 5, 7, 8, 10, 11, 14, 17, 18, 20],
        [0, 7, 10, 12, 13, 18, 19, 20, 21],
        [3, 7, 8, 9, 10, 13, 15, 17, 19, 20],
        [0, 3, 5, 6, 9, 10, 11, 14, 15, 16],
        [0, 1, 5, 6, 9, 11, 12, 19, 20],
        [2, 6, 9, 10, 12, 14, 15, 16, 18, 19],
        [0, 1, 2, 3, 5, 8, 9, 10, 12, 15, 17, 18, 19, 21],
        [0, 1, 4, 5, 8, 9, 11, 15, 16, 17, 18],
        [5, 6, 8, 11, 12, 14, 15, 16],
        [1, 3, 10, 12, 13, 15, 16, 18],
        [1, 4, 5, 6, 7, 8, 11, 12, 15, 18, 20, 21],
        [4, 6, 7, 8, 11, 12, 13, 14, 17, 19, 20, 21],
        [4, 8, 10, 11, 12, 16, 20],
        [1, 2, 6, 7, 8, 9, 10, 11, 12, 14, 16, 20, 21],
    ]

    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, n_packages - 1)
    model.L = pyo.RangeSet(0, n_legs - 1)

    model.x = pyo.Var(model.P, domain=pyo.NonNegativeIntegers)

    def demand_rule(m, p):
        return m.x[p] <= demand[p]
    model.demand_con = pyo.Constraint(model.P, rule=demand_rule)

    def leg_rule(m, l):
        return sum(m.x[p] for p in leg_packages[l]) <= leg_capacity[l]
    model.leg_con = pyo.Constraint(model.L, rule=leg_rule)

    def obj_rule(m):
        return sum(revenue[p] * m.x[p] for p in m.P)
    model.total_revenue = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_revenue))
    return {"objective": obj_val, "status": "optimal"}