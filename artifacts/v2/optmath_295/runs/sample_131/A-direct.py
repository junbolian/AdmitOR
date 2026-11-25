import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    products = [0, 1, 2]
    periods = [0, 1, 2, 3]

    profit = params["profit_per_unit"]
    hold = params["holding_cost"]
    grinder_cap = params["grinder_capacity"]
    drill_cap = params["drill_capacity"]
    borer_cap = params["borer_capacity"]
    max_inv = params["max_inventory"]

    max_sales = {
        0: params["max_sales_p0"],
        1: params["max_sales_p1"],
        2: params["max_sales_p2"],
    }

    final_target = params["final_inventory_target"]

    gtime = {0: params["grinder_time_p0"], 1: params["grinder_time_p1"], 2: params["grinder_time_p2"]}
    dtime = {0: params["drill_time_p0"], 1: params["drill_time_p1"], 2: params["drill_time_p2"]}
    btime = {0: params["borer_time_p0"], 1: params["borer_time_p1"], 2: params["borer_time_p2"]}

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=products)
    model.T = pyo.Set(initialize=periods)

    model.prod = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)
    model.sales = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)
    model.inv = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)

    def inventory_balance_rule(mdl, p, t):
        if t == 0:
            return mdl.prod[p, t] == mdl.sales[p, t] + mdl.inv[p, t]
        return mdl.inv[p, t - 1] + mdl.prod[p, t] == mdl.sales[p, t] + mdl.inv[p, t]
    model.inventory_balance = pyo.Constraint(model.P, model.T, rule=inventory_balance_rule)

    def grinder_rule(mdl, t):
        return sum(gtime[p] * mdl.prod[p, t] for p in mdl.P) <= grinder_cap
    model.grinder_limit = pyo.Constraint(model.T, rule=grinder_rule)

    def drill_rule(mdl, t):
        return sum(dtime[p] * mdl.prod[p, t] for p in mdl.P) <= drill_cap
    model.drill_limit = pyo.Constraint(model.T, rule=drill_rule)

    def borer_rule(mdl, t):
        cap = 0 if t == 2 else borer_cap
        return sum(btime[p] * mdl.prod[p, t] for p in mdl.P) <= cap
    model.borer_limit = pyo.Constraint(model.T, rule=borer_rule)

    def inv_cap_rule(mdl, p, t):
        return mdl.inv[p, t] <= max_inv
    model.inv_cap = pyo.Constraint(model.P, model.T, rule=inv_cap_rule)

    def sales_cap_rule(mdl, p, t):
        return mdl.sales[p, t] <= max_sales[p][t]
    model.sales_cap = pyo.Constraint(model.P, model.T, rule=sales_cap_rule)

    def final_inv_rule(mdl, p):
        return mdl.inv[p, 3] == final_target
    model.final_inv = pyo.Constraint(model.P, rule=final_inv_rule)

    def objective_rule(mdl):
        revenue = sum(profit[p] * mdl.sales[p, t] for p in mdl.P for t in mdl.T)
        holding = sum(hold * mdl.inv[p, t] for p in mdl.P for t in mdl.T)
        return revenue - holding
    model.obj = pyo.Objective(rule=objective_rule, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}