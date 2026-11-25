import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    products = [0, 1]
    periods = [0, 1, 2, 3]

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=products)
    model.T = pyo.Set(initialize=periods)

    model.prod = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)
    model.inv = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)
    model.sales = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)

    profit = {0: params["profit_product0"], 1: params["profit_product1"]}
    holding_cost = params["holding_cost"]

    def obj_rule(m):
        revenue = sum(profit[p] * m.sales[p, t] for p in m.P for t in m.T)
        hold = sum(holding_cost * m.inv[p, t] for p in m.P for t in m.T)
        return revenue - hold

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def balance_rule(m, p, t):
        if t == 0:
            return m.prod[p, t] == m.sales[p, t] + m.inv[p, t]
        return m.inv[p, t - 1] + m.prod[p, t] == m.sales[p, t] + m.inv[p, t]

    model.balance = pyo.Constraint(model.P, model.T, rule=balance_rule)

    grinder_cap = params["grinder_capacity"]
    drill_cap = params["drill_capacity"]
    borer_cap = params["borer_capacity"]

    tg = {0: params["time_product0_grinder"], 1: params["time_product1_grinder"]}
    td = {0: params["time_product0_drill"], 1: params["time_product1_drill"]}
    tb = {0: params["time_product0_borer"], 1: params["time_product1_borer"]}

    def grinder_rule(m, t):
        return sum(tg[p] * m.prod[p, t] for p in m.P) <= grinder_cap

    def drill_rule(m, t):
        return sum(td[p] * m.prod[p, t] for p in m.P) <= drill_cap

    def borer_rule(m, t):
        return sum(tb[p] * m.prod[p, t] for p in m.P) <= borer_cap

    model.grinder = pyo.Constraint(model.T, rule=grinder_rule)
    model.drill = pyo.Constraint(model.T, rule=drill_rule)
    model.borer = pyo.Constraint(model.T, rule=borer_rule)

    inv_limit = params["inventory_limit"]

    def inv_limit_rule(m, p, t):
        return m.inv[p, t] <= inv_limit

    model.inv_limit = pyo.Constraint(model.P, model.T, rule=inv_limit_rule)

    # Sales limits: params may be scalar or per-period lists.
    raw0 = params["sales_limit_product0"]
    raw1 = params["sales_limit_product1"]

    if isinstance(raw0, (list, tuple)):
        sl0 = {t: raw0[t] for t in periods}
    else:
        sl0 = {t: raw0 for t in periods}

    if isinstance(raw1, (list, tuple)):
        sl1 = {t: raw1[t] for t in periods}
    else:
        sl1 = {t: raw1 for t in periods}

    def sales0_rule(m, t):
        return m.sales[0, t] <= sl0[t]

    def sales1_rule(m, t):
        return m.sales[1, t] <= sl1[t]

    model.sales0 = pyo.Constraint(model.T, rule=sales0_rule)
    model.sales1 = pyo.Constraint(model.T, rule=sales1_rule)

    target_inv = params["target_inventory"]

    def target_rule(m, p):
        return m.inv[p, 3] == target_inv

    model.target = pyo.Constraint(model.P, rule=target_rule)

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}