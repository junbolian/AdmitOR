import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_products = 3
    num_periods = 6
    products = range(num_products)
    periods = range(num_periods)

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

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=list(products))
    model.T = pyo.Set(initialize=list(periods))

    model.produce = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)
    model.sell = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)
    model.inventory = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)

    model.revenue = pyo.Expression(
        expr=sum(profit_per_unit[p] * model.sell[p, t]
                 for p in model.P for t in model.T)
    )
    model.holding = pyo.Expression(
        expr=sum(holding_cost_per_unit * model.inventory[p, t]
                 for p in model.P for t in model.T)
    )

    def objective_rule(m):
        return m.revenue - m.holding

    model.total_profit = pyo.Objective(rule=objective_rule, sense=pyo.maximize)

    def balance_period0_rule(m, p):
        return m.produce[p, 0] == m.sell[p, 0] + m.inventory[p, 0]

    model.balance_period0 = pyo.Constraint(model.P, rule=balance_period0_rule)

    def balance_rule(m, p, t):
        if t == 0:
            return pyo.Constraint.Skip
        return m.inventory[p, t - 1] + m.produce[p, t] == m.sell[p, t] + m.inventory[p, t]

    model.balance = pyo.Constraint(model.P, model.T, rule=balance_rule)

    def final_inv_rule(m, p):
        return m.inventory[p, num_periods - 1] == final_inventory[p]

    model.final_inv = pyo.Constraint(model.P, rule=final_inv_rule)

    def inv_cap_rule(m, p, t):
        return m.inventory[p, t] <= max_inventory

    model.inv_cap = pyo.Constraint(model.P, model.T, rule=inv_cap_rule)

    def sales_cap_rule(m, p, t):
        return m.sell[p, t] <= max_sales[p][t]

    model.sales_cap = pyo.Constraint(model.P, model.T, rule=sales_cap_rule)

    def grinder_rule(m, t):
        return sum(grinder_time[p] * m.produce[p, t] for p in m.P) <= grinder_capacity[t]

    model.grinder_cap = pyo.Constraint(model.T, rule=grinder_rule)

    def drill_rule(m, t):
        return sum(drill_time[p] * m.produce[p, t] for p in m.P) <= drill_capacity[t]

    model.drill_cap = pyo.Constraint(model.T, rule=drill_rule)

    def borer_rule(m, t):
        return sum(borer_time[p] * m.produce[p, t] for p in m.P) <= borer_capacity[t]

    model.borer_cap = pyo.Constraint(model.T, rule=borer_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_profit))
    return {"objective": obj_val, "status": "optimal"}