import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit_per_unit = params["profit_per_unit"]
    holding_cost = params["holding_cost"]
    grinder_capacity = params["grinder_capacity"]
    drill_capacity = params["drill_capacity"]
    borer_capacity = params["borer_capacity"]
    machine_time = params["machine_time"]
    max_inventory = params["max_inventory"]
    max_sales = params["max_sales"]
    final_inventory = params["final_inventory"]

    products = list(range(4))
    periods = list(range(6))

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=products)
    model.T = pyo.Set(initialize=periods)

    model.produce = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)
    model.inventory = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)
    model.sales = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(
            profit_per_unit[p] * m.sales[p, t]
            for p in m.P for t in m.T
        ) - sum(
            holding_cost * m.inventory[p, t]
            for p in m.P for t in m.T
        )
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def balance_first_rule(m, p):
        return m.produce[p, 0] == m.sales[p, 0] + m.inventory[p, 0]
    model.balance_first = pyo.Constraint(model.P, rule=balance_first_rule)

    def balance_rule(m, p, t):
        if t == 0:
            return pyo.Constraint.Skip
        return m.inventory[p, t - 1] + m.produce[p, t] == m.sales[p, t] + m.inventory[p, t]
    model.balance = pyo.Constraint(model.P, model.T, rule=balance_rule)

    def grinder_rule(m, t):
        return sum(machine_time["grinder"][p] * m.produce[p, t] for p in m.P) <= grinder_capacity[t]
    model.grinder_cap = pyo.Constraint(model.T, rule=grinder_rule)

    def drill_rule(m, t):
        return sum(machine_time["drill"][p] * m.produce[p, t] for p in m.P) <= drill_capacity[t]
    model.drill_cap = pyo.Constraint(model.T, rule=drill_rule)

    def borer_rule(m, t):
        return sum(machine_time["borer"][p] * m.produce[p, t] for p in m.P) <= borer_capacity[t]
    model.borer_cap = pyo.Constraint(model.T, rule=borer_rule)

    def inv_max_rule(m, p, t):
        return m.inventory[p, t] <= max_inventory
    model.inv_max = pyo.Constraint(model.P, model.T, rule=inv_max_rule)

    def sales_max_rule(m, p, t):
        return m.sales[p, t] <= max_sales[p][t]
    model.sales_max = pyo.Constraint(model.P, model.T, rule=sales_max_rule)

    def final_inv_rule(m, p):
        return m.inventory[p, 5] == final_inventory[p]
    model.final_inv = pyo.Constraint(model.P, rule=final_inv_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}