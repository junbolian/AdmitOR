import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["cost"]
    capacity = params["capacity"]
    demand = params["demand"]
    min_delivery = params["min_delivery"]
    min_contributors = params["min_contributors"]

    nP = len(capacity)
    nC = len(demand)
    producers = range(nP)
    contracts = range(nC)

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=list(producers))
    model.C = pyo.Set(initialize=list(contracts))

    model.x = pyo.Var(model.P, model.C, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.P, model.C, domain=pyo.Binary)

    def obj_rule(m):
        return sum(cost[i][j] * m.x[i, j] for i in m.P for j in m.C)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def demand_rule(m, j):
        return sum(m.x[i, j] for i in m.P) >= demand[j]
    model.demand_con = pyo.Constraint(model.C, rule=demand_rule)

    def cap_rule(m, i):
        return sum(m.x[i, j] for j in m.C) <= capacity[i]
    model.cap_con = pyo.Constraint(model.P, rule=cap_rule)

    def link_lo_rule(m, i, j):
        return m.x[i, j] >= min_delivery[i] * m.y[i, j]
    model.link_lo = pyo.Constraint(model.P, model.C, rule=link_lo_rule)

    def link_hi_rule(m, i, j):
        return m.x[i, j] <= min(capacity[i], demand[j]) * m.y[i, j]
    model.link_hi = pyo.Constraint(model.P, model.C, rule=link_hi_rule)

    def contrib_rule(m, j):
        return sum(m.y[i, j] for i in m.P) >= min_contributors[j]
    model.contrib_con = pyo.Constraint(model.C, rule=contrib_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}