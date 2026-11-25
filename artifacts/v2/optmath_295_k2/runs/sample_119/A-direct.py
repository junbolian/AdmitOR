import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    products = [0, 1, 2, 3]
    periods = [0, 1, 2, 3, 4, 5]

    profit = params["profit"]
    holding_cost = params["holding_cost"]
    grinder_capacity = params["grinder_capacity"]
    drill_capacity = params["drill_capacity"]
    borer_capacity = params["borer_capacity"]
    grinder_time = params["grinder_time"]
    drill_time = params["drill_time"]
    borer_time = params["borer_time"]
    inventory_limit = params["inventory_limit"]
    sales_limit = params["sales_limit"]
    target_inventory = params["target_inventory"]

    model = pyo.ConcreteModel()
    model.P = pyo.Set(initialize=products)
    model.T = pyo.Set(initialize=periods)

    model.prod = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)
    model.inv = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)
    model.sell = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)

    model.obj = pyo.Objective(
        expr=sum(profit[p] * model.sell[p, t] for p in model.P for t in model.T)
        - sum(holding_cost * model.inv[p, t] for p in model.P for t in model.T),
        sense=pyo.maximize,
    )

    def balance_rule(mdl, p, t):
        if t == periods[0]:
            return mdl.prod[p, t] == mdl.sell[p, t] + mdl.inv[p, t]
        return mdl.inv[p, t - 1] + mdl.prod[p, t] == mdl.sell[p, t] + mdl.inv[p, t]

    model.balance = pyo.Constraint(model.P, model.T, rule=balance_rule)

    def grinder_rule(mdl, t):
        return sum(grinder_time[p] * mdl.prod[p, t] for p in mdl.P) <= grinder_capacity

    def drill_rule(mdl, t):
        return sum(drill_time[p] * mdl.prod[p, t] for p in mdl.P) <= drill_capacity

    def borer_rule(mdl, t):
        return sum(borer_time[p] * mdl.prod[p, t] for p in mdl.P) <= borer_capacity[t]

    model.grinder_cap = pyo.Constraint(model.T, rule=grinder_rule)
    model.drill_cap = pyo.Constraint(model.T, rule=drill_rule)
    model.borer_cap = pyo.Constraint(model.T, rule=borer_rule)

    model.inv_limit = pyo.Constraint(
        model.P,
        model.T,
        rule=lambda mdl, p, t: mdl.inv[p, t] <= inventory_limit,
    )

    model.sales_limit = pyo.Constraint(
        model.P,
        model.T,
        rule=lambda mdl, p, t: mdl.sell[p, t] <= sales_limit[p][t],
    )

    model.target = pyo.Constraint(
        model.P,
        rule=lambda mdl, p: mdl.inv[p, periods[-1]] == target_inventory[p],
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}