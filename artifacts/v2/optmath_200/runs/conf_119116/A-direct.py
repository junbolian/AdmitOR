import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit_per_unit = params["profit_per_unit"]
    holding_cost_per_unit = params["holding_cost_per_unit"]
    grinder_hours_per_unit = params["grinder_hours_per_unit"]
    drill_hours_per_unit = params["drill_hours_per_unit"]
    borer_hours_per_unit = params["borer_hours_per_unit"]
    grinder_capacity = params["grinder_capacity"]
    drill_capacity = params["drill_capacity"]
    borer_capacity = params["borer_capacity"]
    inventory_limit = params["inventory_limit"]
    sales_limit = params["sales_limit"]
    final_inventory = params["final_inventory"]

    products = list(range(3))
    periods = list(range(4))

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=products)
    model.T = pyo.Set(initialize=periods)

    model.produce = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)
    model.inventory = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)
    model.sell = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        revenue = sum(profit_per_unit[p] * m.sell[p, t] for p in m.P for t in m.T)
        holding = sum(holding_cost_per_unit * m.inventory[p, t] for p in m.P for t in m.T)
        return revenue - holding

    model.total_profit = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def balance_period0_rule(m, p):
        return m.produce[p, 0] == m.sell[p, 0] + m.inventory[p, 0]

    model.balance_period0 = pyo.Constraint(model.P, rule=balance_period0_rule)

    def balance_rule(m, p, t):
        if t == 0:
            return pyo.Constraint.Skip
        return m.inventory[p, t - 1] + m.produce[p, t] == m.sell[p, t] + m.inventory[p, t]

    model.balance = pyo.Constraint(model.P, model.T, rule=balance_rule)

    def grinder_cap_rule(m, t):
        return sum(grinder_hours_per_unit[p] * m.produce[p, t] for p in m.P) <= grinder_capacity

    model.grinder_cap = pyo.Constraint(model.T, rule=grinder_cap_rule)

    def drill_cap_rule(m, t):
        return sum(drill_hours_per_unit[p] * m.produce[p, t] for p in m.P) <= (0 if t == 0 else drill_capacity)

    model.drill_cap = pyo.Constraint(model.T, rule=drill_cap_rule)

    def borer_cap_rule(m, t):
        return sum(borer_hours_per_unit[p] * m.produce[p, t] for p in m.P) <= borer_capacity

    model.borer_cap = pyo.Constraint(model.T, rule=borer_cap_rule)

    def inventory_limit_rule(m, p, t):
        return m.inventory[p, t] <= inventory_limit

    model.inventory_limit_con = pyo.Constraint(model.P, model.T, rule=inventory_limit_rule)

    def sales_limit_rule(m, p, t):
        return m.sell[p, t] <= sales_limit[t][p]

    model.sales_limit_con = pyo.Constraint(model.P, model.T, rule=sales_limit_rule)

    def final_inventory_rule(m, p):
        return m.inventory[p, 3] == final_inventory[p]

    model.final_inventory_con = pyo.Constraint(model.P, rule=final_inventory_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_profit))
    return {"objective": obj_val, "status": "optimal"}