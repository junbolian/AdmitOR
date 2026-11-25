import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    products = [0, 1]
    periods = [0, 1, 2, 3]

    profit = params["profit_per_unit"]
    holding_cost = params["holding_cost_per_unit"]
    cap_grinder = params["machine_capacity_grinder"]
    cap_drill = params["machine_capacity_drill"]
    cap_borer = params["machine_capacity_borer"]
    time_grinder = params["prod_time_grinder"]
    time_drill = params["prod_time_drill"]
    time_borer = params["prod_time_borer"]
    inv_cap = params["inventory_capacity"]
    sales_limit_0 = params["sales_limit_prod0"]
    sales_limit_1 = params["sales_limit_prod1"]
    target_inv = params["target_inventory"]

    sales_limit = {0: sales_limit_0, 1: sales_limit_1}

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=products)
    model.T = pyo.Set(initialize=periods)

    model.prod = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)
    model.inv = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)
    model.sales = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(profit[p] * m.sales[p, t] for p in m.P for t in m.T) \
            - sum(holding_cost * m.inv[p, t] for p in m.P for t in m.T)

    model.total_profit = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def balance_period0_rule(m, p):
        return m.prod[p, 0] == m.sales[p, 0] + m.inv[p, 0]

    model.balance0 = pyo.Constraint(model.P, rule=balance_period0_rule)

    def balance_rule(m, p, t):
        if t == 0:
            return pyo.Constraint.Skip
        return m.inv[p, t - 1] + m.prod[p, t] == m.sales[p, t] + m.inv[p, t]

    model.balance = pyo.Constraint(model.P, model.T, rule=balance_rule)

    def grinder_rule(m, t):
        return sum(time_grinder[p] * m.prod[p, t] for p in m.P) <= cap_grinder

    model.grinder_cap = pyo.Constraint(model.T, rule=grinder_rule)

    def drill_rule(m, t):
        return sum(time_drill[p] * m.prod[p, t] for p in m.P) <= cap_drill

    model.drill_cap = pyo.Constraint(model.T, rule=drill_rule)

    def borer_rule(m, t):
        return sum(time_borer[p] * m.prod[p, t] for p in m.P) <= cap_borer

    model.borer_cap = pyo.Constraint(model.T, rule=borer_rule)

    def inv_cap_rule(m, p, t):
        return m.inv[p, t] <= inv_cap

    model.inv_limit = pyo.Constraint(model.P, model.T, rule=inv_cap_rule)

    def sales_limit_rule(m, p, t):
        return m.sales[p, t] <= sales_limit[p][t]

    model.sales_limit = pyo.Constraint(model.P, model.T, rule=sales_limit_rule)

    def target_rule(m, p):
        return m.inv[p, 3] == target_inv

    model.target_inv = pyo.Constraint(model.P, rule=target_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_profit))
    return {"objective": obj_val, "status": "optimal"}