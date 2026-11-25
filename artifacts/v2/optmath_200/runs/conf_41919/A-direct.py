import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity = params["capacity"]
    demand = params["demand"]
    cost = params["cost"]
    min_producers = params["min_producers"]
    min_delivery = params["min_delivery"]

    producers = list(range(len(capacity)))
    contracts = list(range(len(demand)))

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=producers, ordered=True)
    model.C = pyo.Set(initialize=contracts, ordered=True)

    model.x = pyo.Var(model.P, model.C, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.P, model.C, domain=pyo.Binary)

    def obj_rule(m):
        return sum(cost[p][c] * m.x[p, c] for p in m.P for c in m.C)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(m, c):
        return sum(m.x[p, c] for p in m.P) >= demand[c]

    model.demand_con = pyo.Constraint(model.C, rule=demand_rule)

    def cap_rule(m, p):
        return sum(m.x[p, c] for c in m.C) <= capacity[p]

    model.cap_con = pyo.Constraint(model.P, rule=cap_rule)

    def minprod_rule(m, c):
        return sum(m.y[p, c] for p in m.P) >= min_producers[c]

    model.minprod_con = pyo.Constraint(model.C, rule=minprod_rule)

    def link_lo_rule(m, p, c):
        return m.x[p, c] >= min_delivery[p] * m.y[p, c]

    model.link_lo_con = pyo.Constraint(model.P, model.C, rule=link_lo_rule)

    def link_hi_rule(m, p, c):
        return m.x[p, c] <= capacity[p] * m.y[p, c]

    model.link_hi_con = pyo.Constraint(model.P, model.C, rule=link_hi_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}