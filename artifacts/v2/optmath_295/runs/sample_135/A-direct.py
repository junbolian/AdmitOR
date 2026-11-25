import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    periods = [0, 1, 2, 3]
    products = [0, 1]

    profit_per_unit = {
        0: params["profit_per_unit_product0"],
        1: params["profit_per_unit_product1"],
    }
    holding_cost = params["holding_cost_per_unit_per_period"]

    # Capacity values are per-period indexed; if the param is scalar, broadcast.
    def broadcast(value):
        if isinstance(value, (list, tuple)):
            return {t: value[t] for t in periods}
        return {t: value for t in periods}

    grinder_capacity = broadcast(params["grinder_capacity_per_period"])
    drill_capacity = broadcast(params["drill_capacity_per_period"])
    borer_capacity = broadcast(params["borer_capacity_per_period"])

    grinder_hours = {
        0: params["grinder_hours_product0"],
        1: params["grinder_hours_product1"],
    }
    drill_hours = {
        0: params["drill_hours_product0"],
        1: params["drill_hours_product1"],
    }
    borer_hours = {
        0: params["borer_hours_product0"],
        1: params["borer_hours_product1"],
    }

    max_inventory = params["max_inventory_per_product_per_period"]

    max_sales = {
        0: broadcast(params["max_sales_product0_per_period"]),
        1: broadcast(params["max_sales_product1_per_period"]),
    }

    terminal_inventory = {
        0: params["terminal_inventory_product0"],
        1: params["terminal_inventory_product1"],
    }

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=products)
    model.T = pyo.Set(initialize=periods)

    model.produce = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)
    model.sell = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)
    model.inventory = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        revenue = sum(
            profit_per_unit[i] * m.sell[i, t] for i in products for t in periods
        )
        cost = sum(holding_cost * m.inventory[i, t] for i in products for t in periods)
        return revenue - cost

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def balance_rule(m, i, t):
        if t == 0:
            return m.produce[i, t] == m.sell[i, t] + m.inventory[i, t]
        return m.inventory[i, t - 1] + m.produce[i, t] == m.sell[i, t] + m.inventory[i, t]

    model.balance = pyo.Constraint(model.P, model.T, rule=balance_rule)

    def grinder_rule(m, t):
        return sum(grinder_hours[i] * m.produce[i, t] for i in products) <= grinder_capacity[t]

    model.grinder = pyo.Constraint(model.T, rule=grinder_rule)

    def drill_rule(m, t):
        return sum(drill_hours[i] * m.produce[i, t] for i in products) <= drill_capacity[t]

    model.drill = pyo.Constraint(model.T, rule=drill_rule)

    def borer_rule(m, t):
        return sum(borer_hours[i] * m.produce[i, t] for i in products) <= borer_capacity[t]

    model.borer = pyo.Constraint(model.T, rule=borer_rule)

    def inv_cap_rule(m, i, t):
        return m.inventory[i, t] <= max_inventory

    model.inv_cap = pyo.Constraint(model.P, model.T, rule=inv_cap_rule)

    def sales_rule(m, i, t):
        return m.sell[i, t] <= max_sales[i][t]

    model.sales_lim = pyo.Constraint(model.P, model.T, rule=sales_rule)

    def terminal_rule(m, i):
        return m.inventory[i, 3] == terminal_inventory[i]

    model.terminal = pyo.Constraint(model.P, rule=terminal_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}