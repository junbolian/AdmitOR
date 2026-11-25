import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    cost = params["cost"]
    capacity = params["capacity"]
    demand = params["demand"]
    min_delivery = params["min_delivery"]
    min_contributors = params["min_contributors"]

    P = list(range(5))
    C = list(range(7))

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=P)
    model.C = pyo.Set(initialize=C)

    model.x = pyo.Var(model.P, model.C, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.P, model.C, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(cost[p][c] * model.x[p, c] for p in P for c in C),
        sense=pyo.minimize,
    )

    def demand_rule(m, c):
        return sum(m.x[p, c] for p in P) >= demand[c]
    model.demand_con = pyo.Constraint(model.C, rule=demand_rule)

    def cap_rule(m, p):
        return sum(m.x[p, c] for c in C) <= capacity[p]
    model.cap_con = pyo.Constraint(model.P, rule=cap_rule)

    def min_del_lo(m, p, c):
        return m.x[p, c] >= min_delivery[p] * m.y[p, c]
    model.min_del_lo = pyo.Constraint(model.P, model.C, rule=min_del_lo)

    def min_del_hi(m, p, c):
        return m.x[p, c] <= capacity[p] * m.y[p, c]
    model.min_del_hi = pyo.Constraint(model.P, model.C, rule=min_del_hi)

    def contrib_rule(m, c):
        return sum(m.y[p, c] for p in P) >= min_contributors[c]
    model.contrib_con = pyo.Constraint(model.C, rule=contrib_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}