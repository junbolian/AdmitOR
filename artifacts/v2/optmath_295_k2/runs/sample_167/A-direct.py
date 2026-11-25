import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cost = params["cost"]
    capacity = params["capacity"]
    demand = params["demand"]
    min_contributors = params["min_contributors"]
    min_delivery = params["min_delivery"]

    n_prod = 6
    n_cont = 6
    prod = list(range(n_prod))
    cont = list(range(n_cont))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(prod, cont, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(prod, cont, domain=pyo.Binary)

    def obj_rule(m):
        return sum(cost[i][j] * m.x[i, j] for i in prod for j in cont)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def cap_rule(m, i):
        return sum(m.x[i, j] for j in cont) <= capacity[i]
    model.cap = pyo.Constraint(prod, rule=cap_rule)

    def dem_rule(m, j):
        return sum(m.x[i, j] for i in prod) >= demand[j]
    model.dem = pyo.Constraint(cont, rule=dem_rule)

    def contrib_rule(m, j):
        return sum(m.y[i, j] for i in prod) >= min_contributors[j]
    model.contrib = pyo.Constraint(cont, rule=contrib_rule)

    def maxlink_rule(m, i, j):
        return m.x[i, j] <= capacity[i] * m.y[i, j]
    model.maxlink = pyo.Constraint(prod, cont, rule=maxlink_rule)

    def minlink_rule(m, i, j):
        return m.x[i, j] >= min_delivery[i] * m.y[i, j]
    model.minlink = pyo.Constraint(prod, cont, rule=minlink_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}