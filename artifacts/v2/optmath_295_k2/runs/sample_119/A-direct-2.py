import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n_products = 4
    n_periods = 6
    products = list(range(n_products))
    periods = list(range(n_periods))

    profit = list(params["profit"])
    holding_cost = params["holding_cost"]

    grinder_capacity = params["grinder_capacity"]
    drill_capacity = params["drill_capacity"]
    borer_capacity = params["borer_capacity"]

    grinder_time = list(params["grinder_time"])
    drill_time = list(params["drill_time"])
    borer_time = list(params["borer_time"])

    inventory_limit = params["inventory_limit"]

    sales_limit_raw = params["sales_limit"]
    sales_limit = {(p, t): sales_limit_raw[p][t] for p in products for t in periods}

    target_inventory_raw = params["target_inventory"]
    target_inventory = {p: target_inventory_raw[p] for p in products}

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=products)
    model.T = pyo.Set(initialize=periods)

    model.produce = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)
    model.inventory = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)
    model.sell = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)

    def obj_rule(mdl):
        revenue = sum(profit[p] * mdl.sell[p, t] for p in mdl.P for t in mdl.T)
        hold = sum(holding_cost * mdl.inventory[p, t] for p in mdl.P for t in mdl.T)
        return revenue - hold

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def balance_rule(mdl, p, t):
        prev_inv = mdl.inventory[p, t - 1] if t > 0 else 0
        return prev_inv + mdl.produce[p, t] == mdl.sell[p, t] + mdl.inventory[p, t]

    model.balance = pyo.Constraint(model.P, model.T, rule=balance_rule)

    def grinder_rule(mdl, t):
        return sum(grinder_time[p] * mdl.produce[p, t] for p in mdl.P) <= grinder_capacity

    model.grinder_cap = pyo.Constraint(model.T, rule=grinder_rule)

    def drill_rule(mdl, t):
        return sum(drill_time[p] * mdl.produce[p, t] for p in mdl.P) <= drill_capacity

    model.drill_cap = pyo.Constraint(model.T, rule=drill_rule)

    def borer_rule(mdl, t):
        borer_avail = 0 if t == 3 else borer_capacity
        return sum(borer_time[p] * mdl.produce[p, t] for p in mdl.P) <= borer_avail

    model.borer_cap = pyo.Constraint(model.T, rule=borer_rule)

    def inv_limit_rule(mdl, p, t):
        return mdl.inventory[p, t] <= inventory_limit

    model.inv_limit = pyo.Constraint(model.P, model.T, rule=inv_limit_rule)

    def sales_limit_rule(mdl, p, t):
        return mdl.sell[p, t] <= sales_limit[p, t]

    model.sales_cap = pyo.Constraint(model.P, model.T, rule=sales_limit_rule)

    def target_rule(mdl, p):
        return mdl.inventory[p, n_periods - 1] == target_inventory[p]

    model.target_inv = pyo.Constraint(model.P, rule=target_rule)

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}