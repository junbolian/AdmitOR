import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["cost"]
    capacity = params["capacity"]
    demand = params["demand"]
    min_contributors = params["min_contributors"]
    min_delivery = params["min_delivery"]

    nP = 6
    nC = 6
    producers = list(range(nP))
    contracts = list(range(nC))

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=producers)
    model.C = pyo.Set(initialize=contracts)

    model.x = pyo.Var(model.P, model.C, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.P, model.C, domain=pyo.Binary)

    def obj_rule(m):
        return sum(cost[p][c] * m.x[p, c] for p in m.P for c in m.C)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Producer capacity
    def cap_rule(m, p):
        return sum(m.x[p, c] for c in m.C) <= capacity[p]

    model.cap = pyo.Constraint(model.P, rule=cap_rule)

    # Contract demand
    def dem_rule(m, c):
        return sum(m.x[p, c] for p in m.P) >= demand[c]

    model.dem = pyo.Constraint(model.C, rule=dem_rule)

    # Min contributors per contract
    def contrib_rule(m, c):
        return sum(m.y[p, c] for p in m.P) >= min_contributors[c]

    model.contrib = pyo.Constraint(model.C, rule=contrib_rule)

    # Linking: if contributing, at least min_delivery; else zero
    def link_upper(m, p, c):
        return m.x[p, c] <= capacity[p] * m.y[p, c]

    def link_lower(m, p, c):
        return m.x[p, c] >= min_delivery[p] * m.y[p, c]

    model.link_upper = pyo.Constraint(model.P, model.C, rule=link_upper)
    model.link_lower = pyo.Constraint(model.P, model.C, rule=link_lower)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}