import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    periods = list(range(4))
    prods = [0, 1]

    profit = {
        0: params["profit_per_unit_product0"],
        1: params["profit_per_unit_product1"],
    }
    hold_cost = params["holding_cost_per_unit_per_period"]

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
    grinder_cap = params["grinder_capacity_per_period"]
    drill_cap = params["drill_capacity_per_period"]
    borer_cap = params["borer_capacity_per_period"]

    max_inv = {
        0: params["max_inventory_product0"],
        1: params["max_inventory_product1"],
    }

    sales_lim = {
        0: params["sales_limit_product0"],
        1: params["sales_limit_product1"],
    }

    target_inv = {
        0: params["target_inventory_product0"],
        1: params["target_inventory_product1"],
    }

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=prods)
    model.T = pyo.Set(initialize=periods)

    model.prod = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)
    model.sales = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)
    model.inv = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)

    def balance_rule(mdl, p, t):
        prev_inv = mdl.inv[p, t - 1] if t > 0 else 0
        return prev_inv + mdl.prod[p, t] == mdl.sales[p, t] + mdl.inv[p, t]

    model.balance = pyo.Constraint(model.P, model.T, rule=balance_rule)

    def grinder_rule(mdl, t):
        return sum(grinder_hours[p] * mdl.prod[p, t] for p in mdl.P) <= grinder_cap

    def drill_rule(mdl, t):
        return sum(drill_hours[p] * mdl.prod[p, t] for p in mdl.P) <= drill_cap

    def borer_rule(mdl, t):
        return sum(borer_hours[p] * mdl.prod[p, t] for p in mdl.P) <= borer_cap

    model.grinder_cap = pyo.Constraint(model.T, rule=grinder_rule)
    model.drill_cap = pyo.Constraint(model.T, rule=drill_rule)
    model.borer_cap = pyo.Constraint(model.T, rule=borer_rule)

    def inv_limit_rule(mdl, p, t):
        return mdl.inv[p, t] <= max_inv[p]

    model.inv_limit = pyo.Constraint(model.P, model.T, rule=inv_limit_rule)

    def sales_limit_rule(mdl, p, t):
        return mdl.sales[p, t] <= sales_lim[p]

    model.sales_limit = pyo.Constraint(model.P, model.T, rule=sales_limit_rule)

    def terminal_rule(mdl, p):
        return mdl.inv[p, 3] == target_inv[p]

    model.terminal_inv = pyo.Constraint(model.P, rule=terminal_rule)

    def obj_rule(mdl):
        revenue = sum(profit[p] * mdl.sales[p, t] for p in mdl.P for t in mdl.T)
        holding = sum(hold_cost * mdl.inv[p, t] for p in mdl.P for t in mdl.T)
        return revenue - holding

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))

    return {"objective": obj_val, "status": "optimal"}