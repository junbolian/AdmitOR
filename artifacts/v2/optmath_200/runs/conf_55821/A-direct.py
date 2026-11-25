import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    products = list(range(4))
    periods = list(range(5))

    profit = params["profit_per_unit"]
    hold_cost = params["holding_cost_per_unit_period"]
    grinder_cap = params["grinder_capacity"]
    drill_cap = params["drill_capacity"]
    borer_cap = params["borer_capacity"]
    max_inv = params["max_inventory"]
    target_inv = params["target_inventory_period4"]
    sales_limits = {
        0: params["sales_limit_product0"],
        1: params["sales_limit_product1"],
        2: params["sales_limit_product2"],
        3: params["sales_limit_product3"],
    }

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=products)
    model.T = pyo.Set(initialize=periods)

    model.prod = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)
    model.inv = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)
    model.sales = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)

    def obj_rule(mdl):
        return sum(
            profit[p] * mdl.sales[p, t] - hold_cost * mdl.inv[p, t]
            for p in mdl.P for t in mdl.T
        )
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    # Inventory balance
    def balance_rule(mdl, p, t):
        if t == 0:
            return mdl.prod[p, t] == mdl.sales[p, t] + mdl.inv[p, t]
        return mdl.inv[p, t - 1] + mdl.prod[p, t] == mdl.sales[p, t] + mdl.inv[p, t]
    model.balance = pyo.Constraint(model.P, model.T, rule=balance_rule)

    # Machine capacity
    def grinder_rule(mdl, t):
        return sum(
            mdl.prod[p, t] * (1 if p in (0, 1) else 2) for p in mdl.P
        ) <= grinder_cap[t]
    model.grinder = pyo.Constraint(model.T, rule=grinder_rule)

    def drill_rule(mdl, t):
        return sum(2 * mdl.prod[p, t] for p in mdl.P) <= drill_cap[t]
    model.drill = pyo.Constraint(model.T, rule=drill_rule)

    def borer_rule(mdl, t):
        return sum(1 * mdl.prod[p, t] for p in mdl.P) <= borer_cap[t]
    model.borer = pyo.Constraint(model.T, rule=borer_rule)

    # Inventory limits
    def inv_limit_rule(mdl, p, t):
        return mdl.inv[p, t] <= max_inv
    model.inv_limit = pyo.Constraint(model.P, model.T, rule=inv_limit_rule)

    # Sales limits
    def sales_limit_rule(mdl, p, t):
        return mdl.sales[p, t] <= sales_limits[p][t]
    model.sales_limit = pyo.Constraint(model.P, model.T, rule=sales_limit_rule)

    # Target ending inventory at period 4
    def target_rule(mdl, p):
        return mdl.inv[p, 4] == target_inv
    model.target = pyo.Constraint(model.P, rule=target_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}