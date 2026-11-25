import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit = params["profit"]
    holding_cost = params["holding_cost"]
    grind_capacity = params["grind_capacity"]
    grind_hours = params["grind_hours"]
    drill_capacity = params["drill_capacity"]
    drill_hours = params["drill_hours"]
    bore_capacity = params["bore_capacity"]
    bore_hours = params["bore_hours"]
    inv_capacity = params["inv_capacity"]
    sales_limit = params["sales_limit"]
    final_inventory = params["final_inventory"]

    products = range(4)
    periods = range(6)

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=products)
    model.T = pyo.Set(initialize=periods)

    model.prod = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)
    model.inv = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)
    model.sales = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(
            profit[p] * m.sales[p, t] - holding_cost * m.inv[p, t]
            for p in m.P for t in m.T
        )
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def balance_first_rule(m, p):
        return m.prod[p, 0] == m.sales[p, 0] + m.inv[p, 0]
    model.balance_first = pyo.Constraint(model.P, rule=balance_first_rule)

    def balance_rule(m, p, t):
        if t == 0:
            return pyo.Constraint.Skip
        return m.inv[p, t - 1] + m.prod[p, t] == m.sales[p, t] + m.inv[p, t]
    model.balance = pyo.Constraint(model.P, model.T, rule=balance_rule)

    def grind_rule(m, t):
        return sum(grind_hours[p] * m.prod[p, t] for p in m.P) <= grind_capacity[t]
    model.grind = pyo.Constraint(model.T, rule=grind_rule)

    def drill_rule(m, t):
        return sum(drill_hours[p] * m.prod[p, t] for p in m.P) <= drill_capacity[t]
    model.drill = pyo.Constraint(model.T, rule=drill_rule)

    def bore_rule(m, t):
        return sum(bore_hours[p] * m.prod[p, t] for p in m.P) <= bore_capacity[t]
    model.bore = pyo.Constraint(model.T, rule=bore_rule)

    def inv_cap_rule(m, p, t):
        if isinstance(inv_capacity, (list, tuple)):
            cap = inv_capacity[p]
        else:
            cap = inv_capacity
        return m.inv[p, t] <= cap
    model.inv_cap = pyo.Constraint(model.P, model.T, rule=inv_cap_rule)

    def sales_cap_rule(m, p, t):
        return m.sales[p, t] <= sales_limit[p][t]
    model.sales_cap = pyo.Constraint(model.P, model.T, rule=sales_cap_rule)

    def final_inv_rule(m, p):
        if isinstance(final_inventory, (list, tuple)):
            req = final_inventory[p]
        else:
            req = final_inventory
        return m.inv[p, 5] == req
    model.final_inv = pyo.Constraint(model.P, rule=final_inv_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {'objective': obj_val, 'status': 'optimal'}