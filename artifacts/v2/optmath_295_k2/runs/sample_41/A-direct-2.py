import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    products = [0, 1, 2]
    periods = [0, 1, 2, 3]

    profits = {
        0: params["profit_product0"],
        1: params["profit_product1"],
        2: params["profit_product2"],
    }
    holding_cost = params["holding_cost"]

    grinder_capacity = params["grinder_capacity"]
    drill_capacity = params["drill_capacity"]
    borer_capacity = params["borer_capacity"]

    grinder_hours = dict(zip(products, params["grinder_hours_per_unit"]))
    drill_hours = dict(zip(products, params["drill_hours_per_unit"]))
    borer_hours = dict(zip(products, params["borer_hours_per_unit"]))

    inventory_capacity = params["inventory_capacity"]
    final_target = params["final_inventory_target"]

    sales_limit = {
        0: params["sales_limit_product0"],
        1: params["sales_limit_product1"],
        2: params["sales_limit_product2"],
    }

    model.P = pyo.Set(initialize=products)
    model.T = pyo.Set(initialize=periods)

    model.produce = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)
    model.inventory = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)
    model.sell = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        revenue = sum(profits[p] * m.sell[p, t] for p in m.P for t in m.T)
        holding = sum(holding_cost * m.inventory[p, t] for p in m.P for t in m.T)
        return revenue - holding

    model.total_profit = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def initial_balance_rule(m, p):
        return m.produce[p, 0] == m.sell[p, 0] + m.inventory[p, 0]

    model.initial_balance = pyo.Constraint(model.P, rule=initial_balance_rule)

    def balance_rule(m, p, t):
        return m.inventory[p, t - 1] + m.produce[p, t] == m.sell[p, t] + m.inventory[p, t]

    model.balance = pyo.Constraint(
        model.P, model.T, rule=lambda m, p, t: pyo.Constraint.Skip if t == 0 else balance_rule(m, p, t)
    )

    def grinder_rule(m, t):
        return sum(grinder_hours[p] * m.produce[p, t] for p in m.P) <= grinder_capacity

    model.grinder_cap = pyo.Constraint(model.T, rule=grinder_rule)

    def drill_rule(m, t):
        return sum(drill_hours[p] * m.produce[p, t] for p in m.P) <= drill_capacity

    model.drill_cap = pyo.Constraint(model.T, rule=drill_rule)

    def borer_rule(m, t):
        return sum(borer_hours[p] * m.produce[p, t] for p in m.P) <= borer_capacity

    model.borer_cap = pyo.Constraint(model.T, rule=borer_rule)

    def inv_cap_rule(m, p, t):
        return m.inventory[p, t] <= inventory_capacity

    model.inv_cap = pyo.Constraint(model.P, model.T, rule=inv_cap_rule)

    def sales_rule(m, p, t):
        return m.sell[p, t] <= sales_limit[p][t]

    model.sales_limit = pyo.Constraint(model.P, model.T, rule=sales_rule)

    def final_target_rule(m, p):
        return m.inventory[p, 3] == final_target

    model.final_target = pyo.Constraint(model.P, rule=final_target_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_profit))
    return {"objective": obj_val, "status": "optimal"}