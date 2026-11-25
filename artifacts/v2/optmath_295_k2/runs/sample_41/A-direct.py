import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    products = [0, 1, 2]
    periods = [0, 1, 2, 3]

    profit = {
        0: params["profit_product0"],
        1: params["profit_product1"],
        2: params["profit_product2"],
    }
    holding_cost = params["holding_cost"]

    grinder_capacity = params["grinder_capacity"]
    drill_capacity = params["drill_capacity"]
    borer_capacity = params["borer_capacity"]

    grinder_hours = params["grinder_hours_per_unit"]
    drill_hours = params["drill_hours_per_unit"]
    borer_hours = params["borer_hours_per_unit"]

    inventory_capacity = params["inventory_capacity"]

    sales_limit = {
        0: params["sales_limit_product0"],
        1: params["sales_limit_product1"],
        2: params["sales_limit_product2"],
    }

    final_inventory_target = params["final_inventory_target"]

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=products)
    model.T = pyo.Set(initialize=periods)

    model.produce = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)
    model.sell = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)
    model.inventory = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)

    def obj_rule(m):
        revenue = sum(profit[p] * m.sell[p, t] for p in m.P for t in m.T)
        hold = sum(holding_cost * m.inventory[p, t] for p in m.P for t in m.T)
        return revenue - hold

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    # Initial inventory balance (period 0)
    def init_balance_rule(m, p):
        return m.produce[p, 0] == m.sell[p, 0] + m.inventory[p, 0]

    model.init_balance = pyo.Constraint(model.P, rule=init_balance_rule)

    # Inventory balance over time
    def balance_rule(m, p, t):
        if t == 0:
            return pyo.Constraint.Skip
        return m.inventory[p, t - 1] + m.produce[p, t] == m.sell[p, t] + m.inventory[p, t]

    model.balance = pyo.Constraint(model.P, model.T, rule=balance_rule)

    # Machine capacity constraints
    def grinder_rule(m, t):
        return sum(grinder_hours[p] * m.produce[p, t] for p in m.P) <= grinder_capacity

    def drill_rule(m, t):
        return sum(drill_hours[p] * m.produce[p, t] for p in m.P) <= drill_capacity

    def borer_rule(m, t):
        return sum(borer_hours[p] * m.produce[p, t] for p in m.P) <= borer_capacity

    model.grinder_cap = pyo.Constraint(model.T, rule=grinder_rule)
    model.drill_cap = pyo.Constraint(model.T, rule=drill_rule)
    model.borer_cap = pyo.Constraint(model.T, rule=borer_rule)

    # Inventory storage limits
    def inv_cap_rule(m, p, t):
        return m.inventory[p, t] <= inventory_capacity

    model.inv_cap = pyo.Constraint(model.P, model.T, rule=inv_cap_rule)

    # Sales limits
    def sales_limit_rule(m, p, t):
        return m.sell[p, t] <= sales_limit[p][t]

    model.sales_cap = pyo.Constraint(model.P, model.T, rule=sales_limit_rule)

    # Final inventory target
    def final_inv_rule(m, p):
        return m.inventory[p, 3] == final_inventory_target

    model.final_inv = pyo.Constraint(model.P, rule=final_inv_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}