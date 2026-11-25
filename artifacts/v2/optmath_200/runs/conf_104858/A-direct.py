import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    revenue = params["revenue"]
    demand = params["demand"]
    flight_capacity = params["flight_capacity"]

    num_packages = 17
    num_legs = 5

    # Which packages use each flight leg
    leg_packages = {
        0: [0, 1, 5, 6, 11, 15, 16],
        1: [1, 8, 16],
        2: [0, 2, 3, 8, 11, 16],
        3: [4, 5, 6, 7, 13, 16],
        4: [1, 2, 4, 5, 6, 8, 11, 12, 13],
    }

    model = pyo.ConcreteModel()

    model.PACKAGES = pyo.RangeSet(0, num_packages - 1)
    model.LEGS = pyo.RangeSet(0, num_legs - 1)

    model.x = pyo.Var(model.PACKAGES, domain=pyo.NonNegativeIntegers)

    def demand_rule(mdl, i):
        return mdl.x[i] <= demand[i]
    model.demand_con = pyo.Constraint(model.PACKAGES, rule=demand_rule)

    def leg_rule(mdl, j):
        return sum(mdl.x[i] for i in leg_packages[j]) <= flight_capacity[j]
    model.leg_con = pyo.Constraint(model.LEGS, rule=leg_rule)

    def obj_rule(mdl):
        return sum(revenue[i] * mdl.x[i] for i in model.PACKAGES)
    model.total_revenue = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_revenue))

    return {"objective": obj_val, "status": "optimal"}