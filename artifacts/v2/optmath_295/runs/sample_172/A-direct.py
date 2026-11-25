import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit_per_unit = params["profit_per_unit"]
    holding_cost = params["holding_cost_per_unit_per_period"]
    machine_capacity = params["machine_capacity_hours"]
    processing_time = params["processing_time_hours"]
    max_inventory = params["max_inventory_per_product"]
    max_sales = params["max_sales_per_product_per_period"]
    target_final_inventory = params["target_final_inventory"]

    products = list(range(3))
    periods = list(range(5))
    machines = list(range(3))

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=products)
    model.T = pyo.Set(initialize=periods)
    model.M = pyo.Set(initialize=machines)

    model.produce = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)
    model.inventory = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)
    model.sell = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(
            profit_per_unit[p] * m.sell[p, t] for p in m.P for t in m.T
        ) - sum(
            holding_cost * m.inventory[p, t] for p in m.P for t in m.T
        )

    model.total_profit = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def init_balance_rule(m, p):
        return m.produce[p, 0] == m.sell[p, 0] + m.inventory[p, 0]

    model.init_balance = pyo.Constraint(model.P, rule=init_balance_rule)

    def balance_rule(m, p, t):
        if t == 0:
            return pyo.Constraint.Skip
        return m.inventory[p, t - 1] + m.produce[p, t] == m.sell[p, t] + m.inventory[p, t]

    model.balance = pyo.Constraint(model.P, model.T, rule=balance_rule)

    def capacity_rule(m, mach, t):
        return sum(
            processing_time[mach][p] * m.produce[p, t] for p in m.P
        ) <= machine_capacity[mach][t]

    model.capacity = pyo.Constraint(model.M, model.T, rule=capacity_rule)

    def inv_limit_rule(m, p, t):
        return m.inventory[p, t] <= max_inventory[p]

    model.inv_limit = pyo.Constraint(model.P, model.T, rule=inv_limit_rule)

    def sales_limit_rule(m, p, t):
        return m.sell[p, t] <= max_sales[p][t]

    model.sales_limit = pyo.Constraint(model.P, model.T, rule=sales_limit_rule)

    def final_inv_rule(m, p):
        return m.inventory[p, 4] == target_final_inventory[p]

    model.final_inv = pyo.Constraint(model.P, rule=final_inv_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_profit))
    return {"objective": obj_val, "status": "optimal"}