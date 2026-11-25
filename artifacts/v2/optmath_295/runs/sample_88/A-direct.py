import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit_per_unit = params["profit_per_unit"]
    holding_cost = params["holding_cost_per_unit_per_period"]
    machine_hours_per_unit = params["machine_hours_per_unit"]
    machine_capacity = params["machine_capacity_per_period"]
    max_inventory = params["max_inventory_per_period"]
    sales_limit_p0 = params["sales_limit_product0"]
    sales_limit_p1 = params["sales_limit_product1"]
    target_final_inventory = params["target_final_inventory"]

    products = [0, 1]
    periods = [0, 1, 2, 3]
    machines = ["Grinder", "Drill", "Borer"]

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=products)
    model.T = pyo.Set(initialize=periods)
    model.M = pyo.Set(initialize=machines)

    model.prod = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)
    model.inv = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)
    model.sales = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)

    def obj_rule(mdl):
        revenue = sum(profit_per_unit[p] * mdl.sales[p, t] for p in products for t in periods)
        hold = sum(holding_cost * mdl.inv[p, t] for p in products for t in periods)
        return revenue - hold

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def balance0_rule(mdl, p):
        return mdl.prod[p, 0] == mdl.sales[p, 0] + mdl.inv[p, 0]

    model.balance0 = pyo.Constraint(model.P, rule=balance0_rule)

    def balance_rule(mdl, p, t):
        if t == 0:
            return pyo.Constraint.Skip
        return mdl.inv[p, t - 1] + mdl.prod[p, t] == mdl.sales[p, t] + mdl.inv[p, t]

    model.balance = pyo.Constraint(model.P, model.T, rule=balance_rule)

    machine_index = {name: i for i, name in enumerate(machines)}

    def cap_rule(mdl, m_name, t):
        row = machine_hours_per_unit[machine_index[m_name]]
        return sum(row[p] * mdl.prod[p, t] for p in products) <= machine_capacity[machine_index[m_name]]

    model.cap = pyo.Constraint(model.M, model.T, rule=cap_rule)

    def invmax_rule(mdl, p, t):
        return mdl.inv[p, t] <= max_inventory

    model.invmax = pyo.Constraint(model.P, model.T, rule=invmax_rule)

    def sales_rule(mdl, p, t):
        if p == 0:
            return mdl.sales[p, t] <= sales_limit_p0[t]
        else:
            return mdl.sales[p, t] <= sales_limit_p1[t]

    model.saleslim = pyo.Constraint(model.P, model.T, rule=sales_rule)

    def final_rule(mdl, p):
        return mdl.inv[p, 3] == target_final_inventory

    model.finalinv = pyo.Constraint(model.P, rule=final_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}