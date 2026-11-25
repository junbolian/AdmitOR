import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    periods = list(range(4))
    products = list(range(3))

    profit = {
        0: params["profit_product_0"],
        1: params["profit_product_1"],
        2: params["profit_product_2"],
    }
    holding_cost = params["holding_cost"]
    max_inventory = params["max_inventory"]

    grinder_cap = {t: params["grinder_capacity"] for t in periods}
    drill_cap = {t: params["drill_capacity"] for t in periods}
    borer_cap = {t: params["borer_capacity"] for t in periods}

    max_sales = {}
    for t in periods:
        for j in products:
            max_sales[(t, j)] = params[f"max_sales_period_{t}_product_{j}"]

    tg = {j: params[f"time_grinder_product_{j}"] for j in products}
    td = {j: params[f"time_drill_product_{j}"] for j in products}
    tb = {j: params[f"time_borer_product_{j}"] for j in products}

    final_inventory_target = params["final_inventory_target"]

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=periods)
    model.J = pyo.Set(initialize=products)

    model.produce = pyo.Var(model.P, model.J, domain=pyo.NonNegativeReals)
    model.sell = pyo.Var(model.P, model.J, domain=pyo.NonNegativeReals)
    model.inventory = pyo.Var(model.P, model.J, domain=pyo.NonNegativeReals)

    def sales_bound(mdl, t, j):
        return mdl.sell[t, j] <= max_sales[(t, j)]
    model.sales_limit = pyo.Constraint(model.P, model.J, rule=sales_bound)

    def inv_bound(mdl, t, j):
        return mdl.inventory[t, j] <= max_inventory
    model.inventory_limit = pyo.Constraint(model.P, model.J, rule=inv_bound)

    def flow_period0(mdl, j):
        return mdl.produce[0, j] == mdl.sell[0, j] + mdl.inventory[0, j]
    model.flow0 = pyo.Constraint(model.J, rule=flow_period0)

    def flow_later(mdl, t, j):
        if t == 0:
            return pyo.Constraint.Skip
        return mdl.inventory[t - 1, j] + mdl.produce[t, j] == mdl.sell[t, j] + mdl.inventory[t, j]
    model.flow = pyo.Constraint(model.P, model.J, rule=flow_later)

    def grinder_cap_rule(mdl, t):
        return sum(tg[j] * mdl.produce[t, j] for j in mdl.J) <= grinder_cap[t]
    model.grinder_cap = pyo.Constraint(model.P, rule=grinder_cap_rule)

    def drill_cap_rule(mdl, t):
        return sum(td[j] * mdl.produce[t, j] for j in mdl.J) <= drill_cap[t]
    model.drill_cap = pyo.Constraint(model.P, rule=drill_cap_rule)

    def borer_cap_rule(mdl, t):
        if t == 2:
            return sum(tb[j] * mdl.produce[t, j] for j in mdl.J) <= 0
        return sum(tb[j] * mdl.produce[t, j] for j in mdl.J) <= borer_cap[t]
    model.borer_cap = pyo.Constraint(model.P, rule=borer_cap_rule)

    def final_inv_rule(mdl, j):
        return mdl.inventory[3, j] == final_inventory_target
    model.final_inv = pyo.Constraint(model.J, rule=final_inv_rule)

    def objective_rule(mdl):
        revenue = sum(profit[j] * mdl.sell[t, j] for t in mdl.P for j in mdl.J)
        holding = holding_cost * sum(mdl.inventory[t, j] for t in mdl.P for j in mdl.J)
        return revenue - holding
    model.total_profit = pyo.Objective(rule=objective_rule, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_profit))

    return {"objective": obj_val, "status": "optimal"}