import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    profit_per_unit = params["profit_per_unit"]
    hold_cost = params["holding_cost_per_unit_per_period"]
    mach_cap = params["machine_capacity_per_period"]
    mach_time = params["machine_time_per_unit"]
    p0_borer_cap = params["period0_borer_capacity"]
    inv_limit = params["inventory_limit_per_product_per_period"]
    sales_limit = params["sales_limit"]
    target_inv = params["target_inventory_end_period4"]

    products = list(range(4))
    periods = list(range(5))
    machines = list(range(3))  # 0=grinder, 1=drill, 2=borer

    model = pyo.ConcreteModel()
    model.P = pyo.Set(initialize=products)
    model.T = pyo.Set(initialize=periods)
    model.M = pyo.Set(initialize=machines)

    model.prod = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)
    model.inv = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)
    model.sell = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)

    def obj_rule(mdl):
        return sum(profit_per_unit[i] * mdl.sell[i, t] for i in mdl.P for t in mdl.T) \
             - sum(hold_cost * mdl.inv[i, t] for i in mdl.P for t in mdl.T)
    model.total_profit = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def init_balance(mdl, i):
        return mdl.prod[i, 0] == mdl.sell[i, 0] + mdl.inv[i, 0]
    model.init_balance_con = pyo.Constraint(model.P, rule=init_balance)

    def inv_balance(mdl, i, t):
        if t == 0:
            return pyo.Constraint.Skip
        return mdl.inv[i, t - 1] + mdl.prod[i, t] == mdl.sell[i, t] + mdl.inv[i, t]
    model.inv_balance_con = pyo.Constraint(model.P, model.T, rule=inv_balance)

    def cap_rule(mdl, k, t):
        if k == 2 and t == 0:
            return sum(mach_time[i][k] * mdl.prod[i, t] for i in mdl.P) <= p0_borer_cap
        return sum(mach_time[i][k] * mdl.prod[i, t] for i in mdl.P) <= mach_cap[k]
    model.cap_con = pyo.Constraint(model.M, model.T, rule=cap_rule)

    def inv_lim_rule(mdl, i, t):
        return mdl.inv[i, t] <= inv_limit
    model.inv_lim_con = pyo.Constraint(model.P, model.T, rule=inv_lim_rule)

    def sales_lim_rule(mdl, i, t):
        return mdl.sell[i, t] <= sales_limit[i][t]
    model.sales_lim_con = pyo.Constraint(model.P, model.T, rule=sales_lim_rule)

    def target_rule(mdl, i):
        return mdl.inv[i, 4] == target_inv[i]
    model.target_con = pyo.Constraint(model.P, rule=target_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_profit))
    return {"objective": obj_val, "status": "optimal"}