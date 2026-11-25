import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit_p0 = params["profit_p0"]
    profit_p1 = params["profit_p1"]
    holding_cost = params["holding_cost"]
    grinder_capacity = params["grinder_capacity"]
    drill_capacity = params["drill_capacity"]
    borer_capacity = params["borer_capacity"]
    grind_p0 = params["grind_hours_per_unit_p0"]
    grind_p1 = params["grind_hours_per_unit_p1"]
    drill_p0 = params["drill_hours_per_unit_p0"]
    drill_p1 = params["drill_hours_per_unit_p1"]
    bore_p0 = params["bore_hours_per_unit_p0"]
    bore_p1 = params["bore_hours_per_unit_p1"]
    inventory_limit = params["inventory_limit"]
    sales_limit_p0 = params["sales_limit_p0"]
    sales_limit_p1 = params["sales_limit_p1"]
    target_inventory = params["target_inventory"]

    periods = list(range(4))
    products = [0, 1]

    model = pyo.ConcreteModel()
    model.P = pyo.Set(initialize=periods)
    model.K = pyo.Set(initialize=products)

    model.prod = pyo.Var(model.P, model.K, within=pyo.NonNegativeReals)
    model.inv = pyo.Var(model.P, model.K, within=pyo.NonNegativeReals)
    model.sales = pyo.Var(model.P, model.K, within=pyo.NonNegativeReals)

    def profit_rule(mdl):
        return sum(
            (profit_p0 if k == 0 else profit_p1) * mdl.sales[t, k]
            for t in mdl.P for k in mdl.K
        ) - sum(holding_cost * mdl.inv[t, k] for t in mdl.P for k in mdl.K)

    model.obj = pyo.Objective(rule=profit_rule, sense=pyo.maximize)

    # Inventory balance (period 0 has no incoming inventory)
    def balance_rule(mdl, t, k):
        if t == 0:
            return mdl.prod[t, k] == mdl.sales[t, k] + mdl.inv[t, k]
        return mdl.inv[t - 1, k] + mdl.prod[t, k] == mdl.sales[t, k] + mdl.inv[t, k]

    model.balance = pyo.Constraint(model.P, model.K, rule=balance_rule)

    def grinder_rule(mdl, t):
        return grind_p0 * mdl.prod[t, 0] + grind_p1 * mdl.prod[t, 1] <= grinder_capacity

    def drill_rule(mdl, t):
        return drill_p0 * mdl.prod[t, 0] + drill_p1 * mdl.prod[t, 1] <= drill_capacity

    def borer_rule(mdl, t):
        return bore_p0 * mdl.prod[t, 0] + bore_p1 * mdl.prod[t, 1] <= borer_capacity

    model.grinder = pyo.Constraint(model.P, rule=grinder_rule)
    model.drill = pyo.Constraint(model.P, rule=drill_rule)
    model.borer = pyo.Constraint(model.P, rule=borer_rule)

    def inv_limit_rule(mdl, t, k):
        return mdl.inv[t, k] <= inventory_limit

    model.inv_limit = pyo.Constraint(model.P, model.K, rule=inv_limit_rule)

    def sales_limit_rule(mdl, t, k):
        limit = sales_limit_p0[t] if k == 0 else sales_limit_p1[t]
        return mdl.sales[t, k] <= limit

    model.sales_limit = pyo.Constraint(model.P, model.K, rule=sales_limit_rule)

    def target_rule(mdl, k):
        return mdl.inv[3, k] == target_inventory

    model.target = pyo.Constraint(model.K, rule=target_rule)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
        return {"objective": obj_val, "status": "optimal"}
    except Exception as e:
        return {"objective": None, "status": "infeasible or failed: " + str(e)[:80]}