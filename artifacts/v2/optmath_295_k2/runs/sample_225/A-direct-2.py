import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    months = list(range(6))
    products = ["A", "B"]

    def cum_demand(prod, month):
        if prod == "A":
            return params["cumulative_demand_A"][month]
        return params["cumulative_demand_B"][month]

    # Monthly demand derived from cumulative demand
    demand = {}
    for prod in products:
        for month in months:
            prev = cum_demand(prod, month - 1) if month > 0 else 0
            demand[(prod, month)] = cum_demand(prod, month) - prev

    def prod_cost(prod, month):
        if prod == "A":
            return params["production_cost_A"][month]
        return params["production_cost_B"][month]

    def setup_cost(prod, month):
        if prod == "A":
            return params["setup_cost_A"][month]
        return params["setup_cost_B"][month]

    def hold_cost(prod, month):
        if prod == "A":
            return params["holding_cost_A"][month]
        return params["holding_cost_B"][month]

    def res_usage(prod):
        if prod == "A":
            return params["resource_usage_A"]
        return params["resource_usage_B"]

    model = pyo.ConcreteModel()
    model.MONTHS = pyo.Set(initialize=months)
    model.PRODUCTS = pyo.Set(initialize=products)

    model.produce = pyo.Var(model.PRODUCTS, model.MONTHS, domain=pyo.NonNegativeReals)
    model.inventory = pyo.Var(model.PRODUCTS, model.MONTHS, domain=pyo.NonNegativeReals)
    model.setup = pyo.Var(model.PRODUCTS, model.MONTHS, domain=pyo.Binary)

    # Inventory balance
    def inv_balance_rule(mdl, p, t):
        prev_inv = mdl.inventory[p, t - 1] if t > 0 else 0
        return mdl.inventory[p, t] == prev_inv + mdl.produce[p, t] - demand[(p, t)]

    model.inv_balance = pyo.Constraint(model.PRODUCTS, model.MONTHS, rule=inv_balance_rule)

    # Terminal inventory zero
    model.terminal_inv = pyo.Constraint(
        model.PRODUCTS, rule=lambda mdl, p: mdl.inventory[p, 5] == 0
    )

    # Production cannot exceed cumulative demand from that month onward
    def prod_upper_rule(mdl, p, t):
        remaining = cum_demand(p, 5) - (cum_demand(p, t - 1) if t > 0 else 0)
        return mdl.produce[p, t] <= remaining

    model.prod_upper = pyo.Constraint(model.PRODUCTS, model.MONTHS, rule=prod_upper_rule)

    # Setup linking
    def setup_link_rule(mdl, p, t):
        remaining = cum_demand(p, 5) - (cum_demand(p, t - 1) if t > 0 else 0)
        return mdl.produce[p, t] <= remaining * mdl.setup[p, t]

    model.setup_link = pyo.Constraint(model.PRODUCTS, model.MONTHS, rule=setup_link_rule)

    # Resource capacity per month
    def resource_rule(mdl, t):
        return sum(res_usage(p) * mdl.produce[p, t] for p in mdl.PRODUCTS) <= params[
            "resource_capacity"
        ][t]

    model.resource = pyo.Constraint(model.MONTHS, rule=resource_rule)

    # Objective
    model.total_cost = pyo.Expression(
        expr=sum(
            prod_cost(p, t) * model.produce[p, t]
            + setup_cost(p, t) * model.setup[p, t]
            + hold_cost(p, t) * model.inventory[p, t]
            for p in model.PRODUCTS
            for t in model.MONTHS
        )
    )

    model.obj = pyo.Objective(expr=model.total_cost, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}