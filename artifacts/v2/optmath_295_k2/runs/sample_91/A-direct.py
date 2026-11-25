import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    m_idx = list(range(4))
    p_idx = [0, 1, 2]

    profit = {
        0: params["profit_per_unit_product_0"],
        1: params["profit_per_unit_product_1"],
        2: params["profit_per_unit_product_2"],
    }
    hold_cost = params["holding_cost_per_unit_per_month"]

    grinder_avail = params["machine_hours_available_grinders"]
    drill_avail = params["machine_hours_available_drills"]
    borer_avail = params["machine_hours_available_borers"]

    tg = {
        0: params["time_grinders_product_0"],
        1: params["time_grinders_product_1"],
        2: params["time_grinders_product_2"],
    }
    td = {
        0: params["time_drills_product_0"],
        1: params["time_drills_product_1"],
        2: params["time_drills_product_2"],
    }
    tb = {
        0: params["time_borers_product_0"],
        1: params["time_borers_product_1"],
        2: params["time_borers_product_2"],
    }

    max_inv = params["max_inventory_per_product"]

    sales_lim = {
        0: params["sales_limits_product_0"],
        1: params["sales_limits_product_1"],
        2: params["sales_limits_product_2"],
    }

    target_inv = params["target_inventory_end_horizon"]

    model = pyo.ConcreteModel()

    model.M = pyo.Set(initialize=m_idx, ordered=True)
    model.P = pyo.Set(initialize=p_idx, ordered=True)
    model.ML = pyo.Set(initialize=[t for t in m_idx if t >= 1], ordered=True)

    model.produce = pyo.Var(model.P, model.M, domain=pyo.NonNegativeReals)
    model.invent = pyo.Var(model.P, model.M, domain=pyo.NonNegativeReals)
    model.sell = pyo.Var(model.P, model.M, domain=pyo.NonNegativeReals)

    def obj_rule(mdl):
        return sum(
            profit[p] * mdl.sell[p, t] - hold_cost * mdl.invent[p, t]
            for p in mdl.P
            for t in mdl.M
        )

    model.total_profit = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def balance_first(mdl, p):
        return mdl.produce[p, 0] == mdl.sell[p, 0] + mdl.invent[p, 0]

    model.balance_first = pyo.Constraint(model.P, rule=balance_first)

    def balance_mid(mdl, p, t):
        return mdl.invent[p, t - 1] + mdl.produce[p, t] == mdl.sell[p, t] + mdl.invent[p, t]

    model.balance_mid = pyo.Constraint(model.P, model.ML, rule=balance_mid)

    def grinder_cap(mdl, t):
        return sum(tg[p] * mdl.produce[p, t] for p in mdl.P) <= grinder_avail[t]

    model.grinder_cap = pyo.Constraint(model.M, rule=grinder_cap)

    def drill_cap(mdl, t):
        return sum(td[p] * mdl.produce[p, t] for p in mdl.P) <= drill_avail[t]

    model.drill_cap = pyo.Constraint(model.M, rule=drill_cap)

    def borer_cap(mdl, t):
        return sum(tb[p] * mdl.produce[p, t] for p in mdl.P) <= borer_avail[t]

    model.borer_cap = pyo.Constraint(model.M, rule=borer_cap)

    def inv_cap(mdl, p, t):
        return mdl.invent[p, t] <= max_inv

    model.inv_cap = pyo.Constraint(model.P, model.M, rule=inv_cap)

    def sale_cap(mdl, p, t):
        return mdl.sell[p, t] <= sales_lim[p][t]

    model.sale_cap = pyo.Constraint(model.P, model.M, rule=sale_cap)

    def final_inv(mdl, p):
        return mdl.invent[p, 3] == target_inv

    model.final_inv = pyo.Constraint(model.P, rule=final_inv)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_profit))
    return {"objective": obj_val, "status": "optimal"}