import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand = params["demand"]
    prod_cost = params["prod_cost"]
    setup_cost = params["setup_cost"]
    hold_cost = params["hold_cost"]
    res_usage = params["res_usage"]
    res_capacity = params["res_capacity"]
    prod_max = params["prod_max"]
    initial_inventory = params["initial_inventory"]

    products = range(len(demand))
    weeks = range(len(res_capacity))

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=list(products))
    model.W = pyo.Set(initialize=list(weeks))

    model.x = pyo.Var(model.P, model.W, domain=pyo.NonNegativeReals)
    model.inv = pyo.Var(model.P, model.W, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.P, model.W, domain=pyo.Binary)

    def obj_rule(m):
        return sum(
            prod_cost[p][w] * m.x[p, w]
            + setup_cost[p][w] * m.y[p, w]
            + hold_cost * m.inv[p, w]
            for p in m.P for w in m.W
        )
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def balance_rule(m, p, w):
        prev = initial_inventory[p] if w == 0 else m.inv[p, w - 1]
        return prev + m.x[p, w] - m.inv[p, w] == demand[p][w]
    model.balance = pyo.Constraint(model.P, model.W, rule=balance_rule)

    def res_rule(m, w):
        return sum(res_usage[p] * m.x[p, w] for p in m.P) <= res_capacity[w]
    model.res = pyo.Constraint(model.W, rule=res_rule)

    def max_rule(m, p, w):
        return m.x[p, w] <= prod_max[p][w] * m.y[p, w]
    model.maxlink = pyo.Constraint(model.P, model.W, rule=max_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}