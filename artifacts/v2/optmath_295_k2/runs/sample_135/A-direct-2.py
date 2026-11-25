import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    periods = [0, 1, 2, 3]
    products = [0, 1]

    profit = {
        0: params["profit_per_unit_p0"],
        1: params["profit_per_unit_p1"],
    }
    holding_cost = params["holding_cost_per_unit_per_period"]

    grinder_cap = params["grinder_capacity_period"]
    drill_cap = params["drill_capacity_period"]
    borer_cap = params["borer_capacity_period"]

    grinder_hours = {
        0: params["grinder_hours_per_unit_p0"],
        1: params["grinder_hours_per_unit_p1"],
    }
    drill_hours = params["drill_hours_per_unit"]
    borer_hours = params["borer_hours_per_unit"]

    max_inv = params["max_inventory_per_product_per_period"]
    max_sales = {
        0: params["max_sales_p0_period"],
        1: params["max_sales_p1_period"],
    }
    final_inv = {
        0: params["final_inventory_p0"],
        1: params["final_inventory_p1"],
    }

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=products)
    model.T = pyo.Set(initialize=periods)

    model.produce = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)
    model.sell = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)
    model.inventory = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)

    model.sales_limit = pyo.Constraint(
        model.P, model.T,
        rule=lambda m, p, t: m.sell[p, t] <= max_sales[p][t],
    )
    model.inv_limit = pyo.Constraint(
        model.P, model.T,
        rule=lambda m, p, t: m.inventory[p, t] <= max_inv,
    )

    def balance_rule(m, p, t):
        prev = 0 if t == 0 else m.inventory[p, t - 1]
        return prev + m.produce[p, t] == m.sell[p, t] + m.inventory[p, t]

    model.balance = pyo.Constraint(model.P, model.T, rule=balance_rule)

    def grinder_rule(m, t):
        return sum(grinder_hours[p] * m.produce[p, t] for p in m.P) <= grinder_cap[t]

    def drill_rule(m, t):
        return sum(drill_hours * m.produce[p, t] for p in m.P) <= drill_cap[t]

    def borer_rule(m, t):
        return sum(borer_hours * m.produce[p, t] for p in m.P) <= borer_cap[t]

    model.grinder = pyo.Constraint(model.T, rule=grinder_rule)
    model.drill = pyo.Constraint(model.T, rule=drill_rule)
    model.borer = pyo.Constraint(model.T, rule=borer_rule)

    model.final_inv = pyo.Constraint(
        model.P,
        rule=lambda m, p: m.inventory[p, 3] == final_inv[p],
    )

    def obj_rule(m):
        return sum(
            profit[p] * m.sell[p, t] - holding_cost * m.inventory[p, t]
            for p in m.P for t in m.T
        )

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}