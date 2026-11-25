import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit_per_unit = params["profit_per_unit"]
    holding_cost = params["holding_cost"]
    grinder_capacity = params["grinder_capacity"]
    drill_capacity = params["drill_capacity"]
    borer_capacity = params["borer_capacity"]
    grinder_time = params["grinder_time"]
    drill_time = params["drill_time"]
    borer_time = params["borer_time"]
    max_inventory = params["max_inventory"]
    max_sales = params["max_sales"]
    final_inventory = params["final_inventory"]

    periods = range(4)
    products = range(3)

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=list(periods))
    model.J = pyo.Set(initialize=list(products))

    model.produce = pyo.Var(model.P, model.J, domain=pyo.NonNegativeReals)
    model.sell = pyo.Var(model.P, model.J, domain=pyo.NonNegativeReals)
    model.inv = pyo.Var(model.P, model.J, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(
            profit_per_unit[j] * m.sell[p, j] for p in m.P for j in m.J
        ) - sum(
            holding_cost * m.inv[p, j] for p in m.P for j in m.J
        )
    model.total_profit = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def balance_period0_rule(m, j):
        return m.produce[0, j] == m.sell[0, j] + m.inv[0, j]
    model.balance_period0 = pyo.Constraint(model.J, rule=balance_period0_rule)

    def balance_rule(m, p, j):
        if p == 0:
            return pyo.Constraint.Skip
        return m.inv[p - 1, j] + m.produce[p, j] == m.sell[p, j] + m.inv[p, j]
    model.balance = pyo.Constraint(model.P, model.J, rule=balance_rule)

    def grinder_rule(m, p):
        return sum(grinder_time[j] * m.produce[p, j] for j in m.J) <= grinder_capacity
    model.grinder_cap = pyo.Constraint(model.P, rule=grinder_rule)

    def drill_rule(m, p):
        return sum(drill_time[j] * m.produce[p, j] for j in m.J) <= drill_capacity[p]
    model.drill_cap = pyo.Constraint(model.P, rule=drill_rule)

    def borer_rule(m, p):
        return sum(borer_time[j] * m.produce[p, j] for j in m.J) <= borer_capacity[p]
    model.borer_cap = pyo.Constraint(model.P, rule=borer_rule)

    def inv_limit_rule(m, p, j):
        return m.inv[p, j] <= max_inventory
    model.inv_limit = pyo.Constraint(model.P, model.J, rule=inv_limit_rule)

    def sales_limit_rule(m, p, j):
        return m.sell[p, j] <= max_sales[p][j]
    model.sales_limit = pyo.Constraint(model.P, model.J, rule=sales_limit_rule)

    def final_inv_rule(m, j):
        return m.inv[3, j] == final_inventory[j]
    model.final_inv = pyo.Constraint(model.J, rule=final_inv_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_profit))
    return {"objective": obj_val, "status": "optimal"}