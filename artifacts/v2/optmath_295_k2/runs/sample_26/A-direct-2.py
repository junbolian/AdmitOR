import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    P = 4
    C = 4
    cap = params["capacity"]
    dem = params["demand"]
    mind = params["min_delivery"]
    cost = params["cost"]

    model = pyo.ConcreteModel()

    model.P = pyo.RangeSet(0, P - 1)
    model.C = pyo.RangeSet(0, C - 1)

    model.x = pyo.Var(model.P, model.C, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.P, model.C, domain=pyo.Binary)

    def obj_rule(m):
        return sum(cost[p][c] * m.x[p, c] for p in m.P for c in m.C)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def cap_rule(m, p):
        return sum(m.x[p, c] for c in m.C) <= cap[p]
    model.cap_con = pyo.Constraint(model.P, rule=cap_rule)

    def dem_rule(m, c):
        return sum(m.x[p, c] for p in m.P) >= dem[c]
    model.dem_con = pyo.Constraint(model.C, rule=dem_rule)

    def minprod_rule(m, c):
        return sum(m.y[p, c] for p in m.P) >= 2
    model.minprod_con = pyo.Constraint(model.C, rule=minprod_rule)

    def link_lb_rule(m, p, c):
        return m.x[p, c] >= mind[p] * m.y[p, c]
    model.link_lb_con = pyo.Constraint(model.P, model.C, rule=link_lb_rule)

    def link_ub_rule(m, p, c):
        return m.x[p, c] <= cap[p] * m.y[p, c]
    model.link_ub_con = pyo.Constraint(model.P, model.C, rule=link_ub_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}