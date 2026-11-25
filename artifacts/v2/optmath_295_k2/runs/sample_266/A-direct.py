import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    products = [0, 1, 2]
    periods = [0, 1, 2, 3, 4, 5]

    profit = params["profit_per_unit"]
    hold_cost = params["holding_cost_per_unit_per_period"]
    grinder_h = params["grinder_hours_per_unit"]
    drill_h = params["drill_hours_per_unit"]
    borer_h = params["borer_hours_per_unit"]
    grinder_cap = params["grinder_capacity_per_period"]
    drill_cap = params["drill_capacity_per_period"]
    borer_cap = params["borer_capacity_per_period"]
    max_inv = params["max_inventory_per_product"]
    max_sales = params["max_sales"]
    final_target = params["final_inventory_target"]

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=products)
    model.T = pyo.Set(initialize=periods)
    model.T1 = pyo.Set(initialize=periods[1:])

    model.produce = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)
    model.invent = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)
    model.sale = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)

    def obj_rule(mdl):
        return sum(profit[p] * mdl.sale[p, t] for p in mdl.P for t in mdl.T) \
            - sum(hold_cost * mdl.invent[p, t] for p in mdl.P for t in mdl.T)
    model.objective = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def balance_first(mdl, p):
        return mdl.produce[p, 0] == mdl.sale[p, 0] + mdl.invent[p, 0]
    model.balance_first = pyo.Constraint(model.P, rule=balance_first)

    def balance_sub(mdl, p, t):
        return mdl.invent[p, t - 1] + mdl.produce[p, t] == mdl.sale[p, t] + mdl.invent[p, t]
    model.balance_sub = pyo.Constraint(model.P, model.T1, rule=balance_sub)

    def grinder_rule(mdl, t):
        return sum(grinder_h[p] * mdl.produce[p, t] for p in mdl.P) <= grinder_cap[t]
    model.grinder_cap = pyo.Constraint(model.T, rule=grinder_rule)

    def drill_rule(mdl, t):
        return sum(drill_h[p] * mdl.produce[p, t] for p in mdl.P) <= drill_cap[t]
    model.drill_cap = pyo.Constraint(model.T, rule=drill_rule)

    def borer_rule(mdl, t):
        return sum(borer_h[p] * mdl.produce[p, t] for p in mdl.P) <= borer_cap[t]
    model.borer_cap = pyo.Constraint(model.T, rule=borer_rule)

    def inv_cap_rule(mdl, p, t):
        return mdl.invent[p, t] <= max_inv[p]
    model.inv_cap = pyo.Constraint(model.P, model.T, rule=inv_cap_rule)

    def sales_cap_rule(mdl, p, t):
        return mdl.sale[p, t] <= max_sales[p][t]
    model.sales_cap = pyo.Constraint(model.P, model.T, rule=sales_cap_rule)

    def final_rule(mdl, p):
        return mdl.invent[p, 5] == final_target[p]
    model.final_inv = pyo.Constraint(model.P, rule=final_rule)

    solver = Highs()
    solver.solve(model)
    obj_val = float(pyo.value(model.objective))
    return {"objective": obj_val, "status": "optimal"}