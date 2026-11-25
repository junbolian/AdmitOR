import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit = params["profit_per_unit"]
    hold_cost = params["holding_cost_per_unit_per_period"]
    cap = params["machine_capacity_per_period"]
    mc_time = params["machine_time_per_unit"]
    p0_borer = params["period0_borer_capacity"]
    inv_lim = params["inventory_limit_per_product_per_period"]
    sales_lim = params["sales_limit"]
    target = params["target_inventory_end_period4"]

    products = list(range(4))
    periods = list(range(5))
    machines = ["grinders", "drills", "borers"]

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=products)
    model.T = pyo.Set(initialize=periods)
    model.M = pyo.Set(initialize=machines)

    def _mc_time(mdl, p, m):
        return mc_time[p][m]

    model.mc_time = pyo.Param(model.P, model.M, initialize=_mc_time, mutable=False)

    model.prod = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)
    model.inv = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)
    model.sell = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)

    def obj_rule(mdl):
        return sum(profit[p] * mdl.sell[p, t] for p in mdl.P for t in mdl.T) \
            - sum(hold_cost * mdl.inv[p, t] for p in mdl.P for t in mdl.T)

    model.total_profit = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def bal0_rule(mdl, p):
        return mdl.prod[p, 0] == mdl.sell[p, 0] + mdl.inv[p, 0]

    model.bal0 = pyo.Constraint(model.P, rule=bal0_rule)

    def bal_rule(mdl, p, t):
        return mdl.inv[p, t - 1] + mdl.prod[p, t] == mdl.sell[p, t] + mdl.inv[p, t]

    model.bal = pyo.Constraint(model.P, model.T, rule=bal_rule)

    def cap_rule(mdl, m, t):
        if m == "borers" and t == 0:
            return sum(mdl.mc_time[p, m] * mdl.prod[p, t] for p in mdl.P) <= p0_borer
        return sum(mdl.mc_time[p, m] * mdl.prod[p, t] for p in mdl.P) <= cap[m]

    model.cap_link = pyo.Constraint(model.M, model.T, rule=cap_rule)

    def inv_lim_rule(mdl, p, t):
        return mdl.inv[p, t] <= inv_lim

    model.inv_lim = pyo.Constraint(model.P, model.T, rule=inv_lim_rule)

    def sales_rule(mdl, p, t):
        return mdl.sell[p, t] <= sales_lim[p][t]

    model.sales_lim = pyo.Constraint(model.P, model.T, rule=sales_rule)

    def target_rule(mdl, p):
        return mdl.inv[p, 4] == target[p]

    model.target = pyo.Constraint(model.P, rule=target_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_profit))
    return {"objective": obj_val, "status": "optimal"}