import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    revenues = params["revenues"]
    demand_limits = params["demand_limits"]
    leg_capacities = params["leg_capacities"]

    n_packages = len(revenues)
    n_legs = len(leg_capacities)

    leg_members = {
        0: [1, 2, 4, 5, 6, 7],
        1: [0, 2, 4, 6, 8, 9, 10],
        2: [2, 3, 4, 10],
        3: [1, 6, 7, 10],
        4: [1, 3, 6, 7, 8, 9],
    }

    model = pyo.ConcreteModel()

    model.PACKAGES = pyo.RangeSet(0, n_packages - 1)
    model.LEGS = pyo.RangeSet(0, n_legs - 1)

    model.x = pyo.Var(model.PACKAGES, domain=pyo.NonNegativeIntegers)

    def obj_rule(m):
        return sum(revenues[i] * m.x[i] for i in m.PACKAGES)

    model.total_revenue = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def demand_rule(m, i):
        return m.x[i] <= demand_limits[i]

    model.demand_con = pyo.Constraint(model.PACKAGES, rule=demand_rule)

    def leg_rule(m, j):
        return sum(m.x[i] for i in leg_members[j]) <= leg_capacities[j]

    model.leg_con = pyo.Constraint(model.LEGS, rule=leg_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_revenue))
    return {"objective": obj_val, "status": "optimal"}