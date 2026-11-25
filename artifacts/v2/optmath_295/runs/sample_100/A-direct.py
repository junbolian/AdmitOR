import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity = params["capacity"]
    demand = params["demand"]
    cost = params["cost"]
    min_delivery = params["min_delivery"]
    min_contributors = params["min_contributors"]

    num_prod = len(capacity)
    num_cont = len(demand)

    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, num_prod - 1)
    model.C = pyo.RangeSet(0, num_cont - 1)

    model.x = pyo.Var(model.P, model.C, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.P, model.C, domain=pyo.Binary)

    def obj_rule(m):
        return sum(cost[i][j] * m.x[i, j] for i in m.P for j in m.C)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def capacity_rule(m, i):
        return sum(m.x[i, j] for j in m.C) <= capacity[i]

    model.capacity_limit = pyo.Constraint(model.P, rule=capacity_rule)

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in m.P) >= demand[j]

    model.demand_req = pyo.Constraint(model.C, rule=demand_rule)

    def link_lo_rule(m, i, j):
        return m.x[i, j] >= min_delivery[i] * m.y[i, j]

    model.link_lo = pyo.Constraint(model.P, model.C, rule=link_lo_rule)

    def link_hi_rule(m, i, j):
        return m.x[i, j] <= capacity[i] * m.y[i, j]

    model.link_hi = pyo.Constraint(model.P, model.C, rule=link_hi_rule)

    def contributors_rule(m, j):
        return sum(m.y[i, j] for i in m.P) >= min_contributors[j]

    model.min_contrib = pyo.Constraint(model.C, rule=contributors_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}