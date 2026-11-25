import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit_per_unit = params["profit_per_unit"]
    holding_cost = params["holding_cost"]
    grinder_capacity = params["grinder_capacity"]
    drill_capacity = params["drill_capacity"]
    borer_capacity = params["borer_capacity"]
    grinder_hours_per_unit = params["grinder_hours_per_unit"]
    drill_hours_per_unit = params["drill_hours_per_unit"]
    borer_hours_per_unit = params["borer_hours_per_unit"]
    inventory_limit = params["inventory_limit"]
    sales_limit_product0 = params["sales_limit_product0"]
    sales_limit_product1 = params["sales_limit_product1"]
    target_inventory = params["target_inventory"]

    products = [0, 1]
    periods = [0, 1, 2, 3]

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=products, ordered=True)
    model.T = pyo.Set(initialize=periods, ordered=True)

    model.prod = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)
    model.inv = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)
    model.sales = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)

    def project_profit(m):
        return sum(
            profit_per_unit[p] * m.sales[p, t] for p in m.P for t in m.T
        ) - sum(
            holding_cost * m.inv[p, t] for p in m.P for t in m.T
        )

    model.revenue_expr = pyo.Expression(rule=project_profit)

    model.maximize_profit = pyo.Objective(rule=lambda m: m.revenue_expr, sense=pyo.maximize)

    def balance_rule(m, p, t):
        if t == 0:
            return m.prod[p, t] == m.sales[p, t] + m.inv[p, t]
        return m.inv[p, t - 1] + m.prod[p, t] == m.sales[p, t] + m.inv[p, t]

    model.balance_con = pyo.Constraint(model.P, model.T, rule=balance_rule)

    def grinder_rule(m, t):
        return sum(grinder_hours_per_unit[p] * m.prod[p, t] for p in m.P) <= grinder_capacity

    def drill_rule(m, t):
        return sum(drill_hours_per_unit[p] * m.prod[p, t] for p in m.P) <= drill_capacity

    def borer_rule(m, t):
        return sum(borer_hours_per_unit[p] * m.prod[p, t] for p in m.P) <= borer_capacity

    model.grinder_con = pyo.Constraint(model.T, rule=grinder_rule)
    model.drill_con = pyo.Constraint(model.T, rule=drill_rule)
    model.borer_con = pyo.Constraint(model.T, rule=borer_rule)

    def inv_limit_rule(m, p, t):
        return m.inv[p, t] <= inventory_limit

    model.inv_limit_con = pyo.Constraint(model.P, model.T, rule=inv_limit_rule)

    def sales_limit_rule(m, p, t):
        if p == 0:
            return m.sales[p, t] <= sales_limit_product0[t]
        return m.sales[p, t] <= sales_limit_product1[t]

    model.sales_limit_con = pyo.Constraint(model.P, model.T, rule=sales_limit_rule)

    def target_rule(m, p):
        return m.inv[p, 3] == target_inventory

    model.target_con = pyo.Constraint(model.P, rule=target_rule)

    Highs().solve(model)

    try:
        obj_val = float(pyo.value(model.maximize_profit))
    except Exception:
        return {"objective": None, "status": "infeasible or no solution"}

    return {"objective": obj_val, "status": "optimal"}