import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit = params["profit_per_unit_sold"]
    hold_cost = params["inventory_holding_cost"]
    hours = params["machine_hours_per_unit"]
    cap = params["machine_capacity_per_period"]
    inv_cap = params["inventory_capacity_per_product"]
    sales_limit = params["sales_limit"]
    target_final = params["target_final_inventory"]

    products = [0, 1, 2]
    periods = [0, 1, 2, 3]
    machines = [0, 1, 2]

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=products)
    model.T = pyo.Set(initialize=periods)
    model.M = pyo.Set(initialize=machines)

    model.produce = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)
    model.inventory = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)
    model.sell = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(profit[p] * m.sell[p, t] for p in m.P for t in m.T) \
            - sum(hold_cost * m.inventory[p, t] for p in m.P for t in m.T)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def balance_rule(m, p, t):
        if t == 0:
            return m.produce[p, t] == m.sell[p, t] + m.inventory[p, t]
        return m.inventory[p, t - 1] + m.produce[p, t] == m.sell[p, t] + m.inventory[p, t]
    model.balance = pyo.Constraint(model.P, model.T, rule=balance_rule)

    def machine_rule(m, mc, t):
        return sum(hours[mc][p] * m.produce[p, t] for p in m.P) <= cap[mc]
    model.machine_cap = pyo.Constraint(model.M, model.T, rule=machine_rule)

    def inv_cap_rule(m, p, t):
        if isinstance(inv_cap, (int, float)):
            return m.inventory[p, t] <= inv_cap
        return m.inventory[p, t] <= inv_cap[p]
    model.inv_cap = pyo.Constraint(model.P, model.T, rule=inv_cap_rule)

    def sales_rule(m, p, t):
        return m.sell[p, t] <= sales_limit[p][t]
    model.sales_cap = pyo.Constraint(model.P, model.T, rule=sales_rule)

    def final_rule(m, p):
        if isinstance(target_final, (int, float)):
            return m.inventory[p, 3] >= target_final
        return m.inventory[p, 3] >= target_final[p]
    model.final_inv = pyo.Constraint(model.P, rule=final_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}