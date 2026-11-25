import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit = params["profit_per_unit"]
    holding_cost = params["holding_cost"]
    grinder_capacity = params["grinder_capacity"]
    drill_capacity = params["drill_capacity"]
    borer_capacity = params["borer_capacity"]
    grinder_hours = params["grinder_hours_per_unit"]
    drill_hours = params["drill_hours_per_unit"]
    borer_hours = params["borer_hours_per_unit"]
    inventory_limit = params["inventory_limit"]
    sales_limit_0 = params["sales_limit_product0"]
    sales_limit_1 = params["sales_limit_product1"]
    target_inventory = params["target_inventory"]

    products = [0, 1]
    periods = [0, 1, 2, 3]
    sales_limits = {0: sales_limit_0, 1: sales_limit_1}

    model = pyo.ConcreteModel()
    model.P = pyo.Set(initialize=products)
    model.T = pyo.Set(initialize=periods)

    model.prod = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)
    model.inv = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)
    model.sale = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(profit[p] * m.sale[p, t] for p in m.P for t in m.T) \
             - sum(holding_cost * m.inv[p, t] for p in m.P for t in m.T)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def balance_rule(m, p, t):
        prev_inv = 0 if t == 0 else m.inv[p, t - 1]
        return prev_inv + m.prod[p, t] == m.sale[p, t] + m.inv[p, t]
    model.balance = pyo.Constraint(model.P, model.T, rule=balance_rule)

    def grinder_rule(m, t):
        return sum(grinder_hours[p] * m.prod[p, t] for p in m.P) <= grinder_capacity
    model.grinder = pyo.Constraint(model.T, rule=grinder_rule)

    def drill_rule(m, t):
        return sum(drill_hours[p] * m.prod[p, t] for p in m.P) <= drill_capacity
    model.drill = pyo.Constraint(model.T, rule=drill_rule)

    def borer_rule(m, t):
        return sum(borer_hours[p] * m.prod[p, t] for p in m.P) <= borer_capacity
    model.borer = pyo.Constraint(model.T, rule=borer_rule)

    def inv_limit_rule(m, p, t):
        return m.inv[p, t] <= inventory_limit
    model.inv_limit = pyo.Constraint(model.P, model.T, rule=inv_limit_rule)

    def sale_limit_rule(m, p, t):
        return m.sale[p, t] <= sales_limits[p][t]
    model.sale_limit = pyo.Constraint(model.P, model.T, rule=sale_limit_rule)

    def target_rule(m, p):
        return m.inv[p, 3] == target_inventory
    model.target = pyo.Constraint(model.P, rule=target_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}