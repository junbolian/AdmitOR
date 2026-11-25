import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n_products = 3
    n_periods = 4
    products = range(n_products)
    periods = range(n_periods)

    revenue = params["revenue"]
    holding_cost = params["holding_cost"]
    grinder_capacity = params["grinder_capacity"]
    drill_capacity = params["drill_capacity"]
    borer_capacity = params["borer_capacity"]
    grinder_time = params["grinder_time"]
    drill_time = params["drill_time"]
    borer_time = params["borer_time"]
    max_inventory = params["max_inventory"]
    sales_limits = params["sales_limits"]
    target_inventory = params["target_inventory"]

    model = pyo.ConcreteModel()

    model.products = pyo.Set(initialize=list(products))
    model.periods = pyo.Set(initialize=list(periods))

    model.produce = pyo.Var(model.periods, model.products, domain=pyo.NonNegativeReals)
    model.inventory = pyo.Var(model.periods, model.products, domain=pyo.NonNegativeReals)
    model.sales = pyo.Var(model.periods, model.products, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(
            revenue[j] * m.sales[t, j] for t in m.periods for j in m.products
        ) - sum(
            holding_cost * m.inventory[t, j] for t in m.periods for j in m.products
        )

    model.profit = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def balance_first_rule(m, j):
        return m.produce[0, j] == m.sales[0, j] + m.inventory[0, j]

    model.balance_first = pyo.Constraint(model.products, rule=balance_first_rule)

    def balance_rule(m, t, j):
        return m.inventory[t - 1, j] + m.produce[t, j] == m.sales[t, j] + m.inventory[t, j]

    model.balance = pyo.Constraint(
        [t for t in periods if t >= 1], model.products, rule=balance_rule
    )

    def grinder_rule(m, t):
        return sum(grinder_time[j] * m.produce[t, j] for j in m.products) <= grinder_capacity

    model.grinder_cap = pyo.Constraint(model.periods, rule=grinder_rule)

    def drill_rule(m, t):
        return sum(drill_time[j] * m.produce[t, j] for j in m.products) <= drill_capacity

    model.drill_cap = pyo.Constraint(model.periods, rule=drill_rule)

    def borer_rule(m, t):
        return sum(borer_time[j] * m.produce[t, j] for j in m.products) <= borer_capacity

    model.borer_cap = pyo.Constraint(model.periods, rule=borer_rule)

    def inv_limit_rule(m, t, j):
        return m.inventory[t, j] <= max_inventory

    model.inv_limit = pyo.Constraint(model.periods, model.products, rule=inv_limit_rule)

    def sales_limit_rule(m, t, j):
        return m.sales[t, j] <= sales_limits[t][j]

    model.sales_limit = pyo.Constraint(model.periods, model.products, rule=sales_limit_rule)

    def target_rule(m, j):
        return m.inventory[n_periods - 1, j] == target_inventory[j]

    model.target_inv = pyo.Constraint(model.products, rule=target_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.profit))
    return {"objective": obj_val, "status": "optimal"}