import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    products = range(3)
    periods = range(5)

    model.P = pyo.Set(initialize=products)
    model.T = pyo.Set(initialize=periods)

    profit = params["profit_per_unit"]
    hold_cost = params["holding_cost_per_unit_per_period"]
    grinder_hours = params["grinder_hours_per_unit"]
    drill_hours = params["drill_hours_per_unit"]
    borer_hours = params["borer_hours_per_unit"]
    grinder_cap = params["grinder_capacity_per_period"]
    drill_cap = params["drill_capacity_per_period"]
    borer_cap = params["borer_capacity_per_period"]
    max_inv = params["max_inventory_per_product"]
    sales_limits = [
        params["sales_limits_product0"],
        params["sales_limits_product1"],
        params["sales_limits_product2"],
    ]
    target_end = params["target_inventory_end_period4"]

    model.prod = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)
    model.inv = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)
    model.sales = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)

    def obj_rule(mdl):
        revenue = sum(profit[p] * mdl.sales[p, t] for p in mdl.P for t in mdl.T)
        holding = sum(hold_cost * mdl.inv[p, t] for p in mdl.P for t in mdl.T)
        return revenue - holding

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def initial_balance_rule(mdl, p):
        return mdl.prod[p, 0] == mdl.sales[p, 0] + mdl.inv[p, 0]

    model.initial_balance = pyo.Constraint(model.P, rule=initial_balance_rule)

    def inv_balance_rule(mdl, p, t):
        return mdl.inv[p, t - 1] + mdl.prod[p, t] == mdl.sales[p, t] + mdl.inv[p, t]

    model.inv_balance = pyo.Constraint(
        model.P, [t for t in periods if t >= 1], rule=inv_balance_rule
    )

    def grinder_rule(mdl, t):
        return (
            sum(grinder_hours[p] * mdl.prod[p, t] for p in mdl.P)
            <= grinder_cap[t]
        )

    def drill_rule(mdl, t):
        return (
            sum(drill_hours[p] * mdl.prod[p, t] for p in mdl.P)
            <= drill_cap[t]
        )

    def borer_rule(mdl, t):
        return (
            sum(borer_hours[p] * mdl.prod[p, t] for p in mdl.P)
            <= borer_cap[t]
        )

    model.grinder_cap = pyo.Constraint(model.T, rule=grinder_rule)
    model.drill_cap = pyo.Constraint(model.T, rule=drill_rule)
    model.borer_cap = pyo.Constraint(model.T, rule=borer_rule)

    def inv_limit_rule(mdl, p, t):
        return mdl.inv[p, t] <= max_inv

    model.inv_limit = pyo.Constraint(model.P, model.T, rule=inv_limit_rule)

    def sales_limit_rule(mdl, p, t):
        return mdl.sales[p, t] <= sales_limits[p][t]

    model.sales_limit = pyo.Constraint(model.P, model.T, rule=sales_limit_rule)

    def target_rule(mdl, p):
        return mdl.inv[p, 4] == target_end

    model.target_inv = pyo.Constraint(model.P, rule=target_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}