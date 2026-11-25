import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit_per_unit = params["profit_per_unit"]
    holding_cost_per_unit = params["holding_cost_per_unit"]
    grinder_time = params["grinder_time"]
    drill_time = params["drill_time"]
    borer_time = params["borer_time"]
    grinder_capacity = params["grinder_capacity"]
    drill_capacity = params["drill_capacity"]
    borer_capacity = params["borer_capacity"]
    max_inventory = params["max_inventory"]
    max_sales = params["max_sales"]
    final_inventory = params["final_inventory"]

    num_products = 3
    num_periods = 6
    products = range(num_products)
    periods = range(num_periods)

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=list(products))
    model.T = pyo.Set(initialize=list(periods))

    model.manufacture = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)
    model.sell = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)
    model.inventory = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(
            profit_per_unit[p] * m.sell[p, t] for p in m.P for t in m.T
        ) - sum(
            holding_cost_per_unit * m.inventory[p, t] for p in m.P for t in m.T
        )

    model.revenue = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def balance_first_rule(m, p):
        return m.manufacture[p, 0] == m.sell[p, 0] + m.inventory[p, 0]

    model.balance_first = pyo.Constraint(model.P, rule=balance_first_rule)

    def balance_rule(m, p, t):
        if t == 0:
            return pyo.Constraint.Skip
        return m.inventory[p, t - 1] + m.manufacture[p, t] == m.sell[p, t] + m.inventory[p, t]

    model.balance = pyo.Constraint(model.P, model.T, rule=balance_rule)

    def grinder_rule(m, t):
        return sum(grinder_time[p] * m.manufacture[p, t] for p in m.P) <= grinder_capacity[t]

    model.grinder_cap = pyo.Constraint(model.T, rule=grinder_rule)

    def drill_rule(m, t):
        return sum(drill_time[p] * m.manufacture[p, t] for p in m.P) <= drill_capacity[t]

    model.drill_cap = pyo.Constraint(model.T, rule=drill_rule)

    def borer_rule(m, t):
        return sum(borer_time[p] * m.manufacture[p, t] for p in m.P) <= borer_capacity[t]

    model.borer_cap = pyo.Constraint(model.T, rule=borer_rule)

    def inv_cap_rule(m, p, t):
        return m.inventory[p, t] <= max_inventory[p]

    model.inv_cap = pyo.Constraint(model.P, model.T, rule=inv_cap_rule)

    def sales_cap_rule(m, p, t):
        return m.sell[p, t] <= max_sales[p][t]

    model.sales_cap = pyo.Constraint(model.P, model.T, rule=sales_cap_rule)

    def final_inv_rule(m, p):
        return m.inventory[p, num_periods - 1] == final_inventory[p]

    model.final_inv = pyo.Constraint(model.P, rule=final_inv_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.revenue))

    return {"objective": obj_val, "status": "optimal"}