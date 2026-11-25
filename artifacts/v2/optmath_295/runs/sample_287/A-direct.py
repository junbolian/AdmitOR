import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    aircraft = list(range(5))
    routes = list(range(5))

    availability = params["availability"]
    demand = params["demand"]
    capacity = params["capacity"]
    cost = params["cost"]

    model = pyo.ConcreteModel()

    model.A = pyo.Set(initialize=aircraft)
    model.R = pyo.Set(initialize=routes)

    model.x = pyo.Var(model.A, model.R, domain=pyo.NonNegativeIntegers)

    def availability_rule(m, a):
        return sum(m.x[a, r] for r in m.R) <= availability[a]

    model.availability_con = pyo.Constraint(model.A, rule=availability_rule)

    def demand_rule(m, r):
        return sum(capacity[a][r] * m.x[a, r] for a in m.A) >= demand[r]

    model.demand_con = pyo.Constraint(model.R, rule=demand_rule)

    def obj_rule(m):
        return sum(cost[a][r] * m.x[a, r] for a in m.A for r in m.R)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))

    return {"objective": obj_val, "status": "optimal"}