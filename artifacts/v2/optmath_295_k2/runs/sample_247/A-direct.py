import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    P = 4  # products
    T = 6  # periods

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

    model = pyo.ConcreteModel()

    model.Prod = pyo.RangeSet(0, P - 1)
    model.Per = pyo.RangeSet(0, T - 1)

    model.prod = pyo.Var(model.Prod, model.Per, domain=pyo.NonNegativeReals)
    model.inv = pyo.Var(model.Prod, model.Per, domain=pyo.NonNegativeReals)
    model.sales = pyo.Var(model.Prod, model.Per, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(profit[p] * m.sales[p, t] for p in m.Prod for t in m.Per) \
            - sum(holding_cost * m.inv[p, t] for p in m.Prod for t in m.Per)
    model.total_profit = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    # Inventory balance
    def balance_rule(m, p, t):
        if t == 0:
            return m.prod[p, t] == m.sales[p, t] + m.inv[p, t]
        return m.inv[p, t - 1] + m.prod[p, t] == m.sales[p, t] + m.inv[p, t]
    model.balance_con = pyo.Constraint(model.Prod, model.Per, rule=balance_rule)

    # Final inventory requirement
    def final_rule(m, p):
        return m.inv[p, T - 1] == final_inventory[p]
    model.final_con = pyo.Constraint(model.Prod, rule=final_rule)

    # Grinding capacity
    def grind_rule(m, t):
        return sum(grind_hours[p] * m.prod[p, t] for p in m.Prod) <= grind_capacity[t]
    model.grind_con = pyo.Constraint(model.Per, rule=grind_rule)

    # Drilling capacity
    def drill_rule(m, t):
        return sum(drill_hours[p] * m.prod[p, t] for p in m.Prod) <= drill_capacity[t]
    model.drill_con = pyo.Constraint(model.Per, rule=drill_rule)

    # Boring capacity
    def bore_rule(m, t):
        return sum(bore_hours[p] * m.prod[p, t] for p in m.Prod) <= bore_capacity[t]
    model.bore_con = pyo.Constraint(model.Per, rule=bore_rule)

    # Inventory capacity
    def invcap_rule(m, p, t):
        return m.inv[p, t] <= inv_capacity
    model.invcap_con = pyo.Constraint(model.Prod, model.Per, rule=invcap_rule)

    # Sales limits
    def sales_rule(m, p, t):
        return m.sales[p, t] <= sales_limit[p][t]
    model.sales_con = pyo.Constraint(model.Prod, model.Per, rule=sales_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_profit))
    return {"objective": obj_val, "status": "optimal"}