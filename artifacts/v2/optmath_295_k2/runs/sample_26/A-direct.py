import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity = params["capacity"]
    demand = params["demand"]
    min_delivery = params["min_delivery"]
    cost = params["cost"]

    producers = list(range(4))
    contracts = list(range(4))

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=producers)
    model.C = pyo.Set(initialize=contracts)

    model.x = pyo.Var(model.P, model.C, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.P, model.C, domain=pyo.Binary)

    def obj_rule(m):
        return sum(cost[p][c] * m.x[p, c] for p in m.P for c in m.C)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def capacity_rule(m, p):
        return sum(m.x[p, c] for c in m.C) <= capacity[p]
    model.capacity_con = pyo.Constraint(model.P, rule=capacity_rule)

    def demand_rule(m, c):
        return sum(m.x[p, c] for p in m.P) >= demand[c]
    model.demand_con = pyo.Constraint(model.C, rule=demand_rule)

    def link_lower_rule(m, p, c):
        return m.x[p, c] >= min_delivery[p] * m.y[p, c]
    model.link_lower = pyo.Constraint(model.P, model.C, rule=link_lower_rule)

    def link_upper_rule(m, p, c):
        return m.x[p, c] <= capacity[p] * m.y[p, c]
    model.link_upper = pyo.Constraint(model.P, model.C, rule=link_upper_rule)

    def min_producers_rule(m, c):
        return sum(m.y[p, c] for p in m.P) >= 2
    model.min_producers = pyo.Constraint(model.C, rule=min_producers_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}