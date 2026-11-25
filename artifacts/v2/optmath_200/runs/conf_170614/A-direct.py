import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    P = range(3)
    C = range(4)

    capacity = {i: params["capacity_%d" % i] for i in P}
    demand = {j: params["demand_%d" % j] for j in C}
    cost = {(i, j): params["cost_%d_%d" % (i, j)] for i in P for j in C}
    min_delivery = {i: params["min_delivery_%d" % i] for i in P}
    min_producers = params["min_producers_per_contract"]

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=list(P))
    model.C = pyo.Set(initialize=list(C))

    model.x = pyo.Var(model.P, model.C, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.P, model.C, domain=pyo.Binary)

    def obj_rule(m):
        return sum(cost[i, j] * m.x[i, j] for i in m.P for j in m.C)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # capacity per producer
    def cap_rule(m, i):
        return sum(m.x[i, j] for j in m.C) <= capacity[i]
    model.cap = pyo.Constraint(model.P, rule=cap_rule)

    # demand satisfaction per contract
    def demand_rule(m, j):
        return sum(m.x[i, j] for i in m.P) >= demand[j]
    model.dem = pyo.Constraint(model.C, rule=demand_rule)

    # linking: min delivery if assigned, zero if not
    def link_lo_rule(m, i, j):
        return m.x[i, j] >= min_delivery[i] * m.y[i, j]
    model.link_lo = pyo.Constraint(model.P, model.C, rule=link_lo_rule)

    def link_hi_rule(m, i, j):
        return m.x[i, j] <= capacity[i] * m.y[i, j]
    model.link_hi = pyo.Constraint(model.P, model.C, rule=link_hi_rule)

    # minimum producers per contract
    def minprod_rule(m, j):
        return sum(m.y[i, j] for i in m.P) >= min_producers
    model.minprod = pyo.Constraint(model.C, rule=minprod_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}