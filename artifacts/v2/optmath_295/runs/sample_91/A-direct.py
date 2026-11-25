import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    products = [0, 1, 2]
    months = [0, 1, 2, 3]

    profit = params["profit_per_unit"]
    hold_cost = params["holding_cost_per_unit_month"]
    cap_grinder = params["machine_hours_grinder"]
    cap_drill = params["machine_hours_drill"]
    cap_borer = params["machine_hours_borer"]
    time_grinder = params["machine_time_grinder"]
    time_drill = params["machine_time_drill"]
    time_borer = params["machine_time_borer"]
    max_inv = params["max_inventory"]
    sales_lim = params["sales_limit"]
    target_final = params["target_final_inventory"]

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=products)
    model.M = pyo.Set(initialize=months)
    model.Mrest = pyo.Set(initialize=[t for t in months if t >= 1])

    model.prod = pyo.Var(model.P, model.M, within=pyo.NonNegativeReals)
    model.inv = pyo.Var(model.P, model.M, within=pyo.NonNegativeReals)
    model.sale = pyo.Var(model.P, model.M, within=pyo.NonNegativeReals)

    def obj_rule(mdl):
        return sum(
            profit[p] * mdl.sale[p, t] - hold_cost * mdl.inv[p, t]
            for p in mdl.P for t in mdl.M
        )
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def balance_first(mdl, p):
        return mdl.prod[p, 0] == mdl.sale[p, 0] + mdl.inv[p, 0]
    model.balance_first = pyo.Constraint(model.P, rule=balance_first)

    def balance_other(mdl, p, t):
        return mdl.inv[p, t - 1] + mdl.prod[p, t] == mdl.sale[p, t] + mdl.inv[p, t]
    model.balance_other = pyo.Constraint(model.P, model.Mrest, rule=balance_other)

    def cap_grinder_rule(mdl, t):
        return sum(time_grinder[p] * mdl.prod[p, t] for p in mdl.P) <= cap_grinder[t]
    model.cap_grinder = pyo.Constraint(model.M, rule=cap_grinder_rule)

    def cap_drill_rule(mdl, t):
        return sum(time_drill[p] * mdl.prod[p, t] for p in mdl.P) <= cap_drill[t]
    model.cap_drill = pyo.Constraint(model.M, rule=cap_drill_rule)

    def cap_borer_rule(mdl, t):
        return sum(time_borer[p] * mdl.prod[p, t] for p in mdl.P) <= cap_borer[t]
    model.cap_borer = pyo.Constraint(model.M, rule=cap_borer_rule)

    def inv_limit(mdl, p, t):
        return mdl.inv[p, t] <= max_inv
    model.inv_limit = pyo.Constraint(model.P, model.M, rule=inv_limit)

    def sale_limit(mdl, p, t):
        return mdl.sale[p, t] <= sales_lim[p][t]
    model.sale_limit = pyo.Constraint(model.P, model.M, rule=sale_limit)

    def final_inv(mdl, p):
        return mdl.inv[p, 3] == target_final[p]
    model.final_inv = pyo.Constraint(model.P, rule=final_inv)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}