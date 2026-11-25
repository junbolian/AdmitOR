import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit_per_unit = params["profit_per_unit"]
    holding_cost = params["holding_cost"]
    machine_hours_grinders = params["machine_hours_grinders"]
    machine_hours_drills = params["machine_hours_drills"]
    machine_hours_borers = params["machine_hours_borers"]
    time_req_grinders = params["time_req_grinders"]
    time_req_drills = params["time_req_drills"]
    time_req_borers = params["time_req_borers"]
    inventory_capacity = params["inventory_capacity"]
    sales_limit_p0 = params["sales_limit_p0"]
    sales_limit_p1 = params["sales_limit_p1"]
    sales_limit_p2 = params["sales_limit_p2"]
    target_inventory = params["target_inventory"]

    products = [0, 1, 2]
    periods = [0, 1, 2, 3, 4]

    sales_caps = {0: sales_limit_p0, 1: sales_limit_p1, 2: sales_limit_p2}
    gr_req = {0: time_req_grinders[0], 1: time_req_grinders[1], 2: time_req_grinders[2]}
    dr_req = {0: time_req_drills[0], 1: time_req_drills[1], 2: time_req_drills[2]}
    br_req = {0: time_req_borers[0], 1: time_req_borers[1], 2: time_req_borers[2]}
    profit = {0: profit_per_unit[0], 1: profit_per_unit[1], 2: profit_per_unit[2]}

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=products)
    model.T = pyo.Set(initialize=periods)

    model.x = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)
    model.I = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)
    model.S = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)

    model.obj = pyo.Objective(
        expr=sum(profit[p] * model.S[p, t] for p in products for t in periods)
        - sum(holding_cost * model.I[p, t] for p in products for t in periods),
        sense=pyo.maximize,
    )

    def init_balance_rule(model, p):
        return model.x[p, 0] == model.S[p, 0] + model.I[p, 0]

    model.init_balance = pyo.Constraint(model.P, rule=init_balance_rule)

    def inv_balance_rule(model, p, t):
        if t >= 1:
            return model.I[p, t - 1] + model.x[p, t] == model.S[p, t] + model.I[p, t]
        return pyo.Constraint.Skip

    model.inv_balance = pyo.Constraint(model.P, model.T, rule=inv_balance_rule)

    def grinder_rule(model, t):
        return sum(gr_req[p] * model.x[p, t] for p in products) <= machine_hours_grinders[t]

    def drill_rule(model, t):
        return sum(dr_req[p] * model.x[p, t] for p in products) <= machine_hours_drills[t]

    def borer_rule(model, t):
        return sum(br_req[p] * model.x[p, t] for p in products) <= machine_hours_borers[t]

    model.grinder_cap = pyo.Constraint(model.T, rule=grinder_rule)
    model.drill_cap = pyo.Constraint(model.T, rule=drill_rule)
    model.borer_cap = pyo.Constraint(model.T, rule=borer_rule)

    def inv_cap_rule(model, p, t):
        return model.I[p, t] <= inventory_capacity

    model.inv_cap = pyo.Constraint(model.P, model.T, rule=inv_cap_rule)

    def sales_rule(model, p, t):
        return model.S[p, t] <= sales_caps[p][t]

    model.sales_cap = pyo.Constraint(model.P, model.T, rule=sales_rule)

    def target_rule(model, p):
        return model.I[p, 4] == target_inventory

    model.target_inv = pyo.Constraint(model.P, rule=target_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}