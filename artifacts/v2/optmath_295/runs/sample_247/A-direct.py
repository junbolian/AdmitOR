import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit_per_unit = params["profit_per_unit"]
    holding_cost = params["holding_cost"]
    grinding_capacity = params["grinding_capacity"]
    grinding_hours_per_unit = params["grinding_hours_per_unit"]
    drilling_capacity = params["drilling_capacity"]
    drilling_hours_per_unit = params["drilling_hours_per_unit"]
    boring_capacity = params["boring_capacity"]
    boring_hours_per_unit = params["boring_hours_per_unit"]
    max_inventory = params["max_inventory"]
    sales_limit = params["sales_limit"]
    final_inventory = params["final_inventory"]

    products = list(range(4))
    periods = list(range(6))

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=products)
    model.T = pyo.Set(initialize=periods)

    model.prod = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)
    model.inv = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)
    model.sale = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(profit_per_unit[i] * m.sale[i, t] for i in m.P for t in m.T) \
               - sum(holding_cost * m.inv[i, t] for i in m.P for t in m.T)
    model.total_profit = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def inv_balance_first(m, i):
        return m.prod[i, 0] == m.sale[i, 0] + m.inv[i, 0]
    model.balance_first = pyo.Constraint(model.P, rule=inv_balance_first)

    def inv_balance(m, i, t):
        if t == 0:
            return pyo.Constraint.Skip
        return m.inv[i, t - 1] + m.prod[i, t] == m.sale[i, t] + m.inv[i, t]
    model.balance = pyo.Constraint(model.P, model.T, rule=inv_balance)

    def grinding_rule(m, t):
        return sum(grinding_hours_per_unit[i] * m.prod[i, t] for i in m.P) <= grinding_capacity[t]
    model.grinding = pyo.Constraint(model.T, rule=grinding_rule)

    def drilling_rule(m, t):
        return sum(drilling_hours_per_unit[i] * m.prod[i, t] for i in m.P) <= drilling_capacity[t]
    model.drilling = pyo.Constraint(model.T, rule=drilling_rule)

    def boring_rule(m, t):
        return sum(boring_hours_per_unit[i] * m.prod[i, t] for i in m.P) <= boring_capacity[t]
    model.boring = pyo.Constraint(model.T, rule=boring_rule)

    def inv_cap(m, i, t):
        return m.inv[i, t] <= max_inventory
    model.inv_cap = pyo.Constraint(model.P, model.T, rule=inv_cap)

    def sale_cap(m, i, t):
        return m.sale[i, t] <= sales_limit[i][t]
    model.sale_cap = pyo.Constraint(model.P, model.T, rule=sale_cap)

    def final_inv_rule(m, i):
        return m.inv[i, len(periods) - 1] == final_inventory[i]
    model.final_inv = pyo.Constraint(model.P, rule=final_inv_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_profit))
    return {"objective": obj_val, "status": "optimal"}