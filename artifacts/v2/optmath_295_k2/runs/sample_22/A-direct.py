import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    P = 3  # products
    T = 5  # periods

    profit = params["profit_per_unit"]
    hold_cost = params["holding_cost_per_unit_per_period"]
    grinder_hours = params["grinder_hours"]
    drill_hours = params["drill_hours"]
    borer_hours = params["borer_hours"]
    mt_grinder = params["machine_time_grinder"]
    mt_drill = params["machine_time_drill"]
    mt_borer = params["machine_time_borer"]
    inv_cap = params["inventory_capacity"]
    sales_limit = params["sales_limit"]
    target_final = params["target_final_inventory"]

    model = pyo.ConcreteModel()
    model.P = pyo.RangeSet(0, P - 1)
    model.T = pyo.RangeSet(0, T - 1)

    model.produce = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)
    model.inventory = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)
    model.sales = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)

    model.obj_expr = pyo.Expression(expr=sum(
        profit[p] * model.sales[p, t] - hold_cost * model.inventory[p, t]
        for p in model.P for t in model.T
    ))
    model.obj = pyo.Objective(expr=model.obj_expr, sense=pyo.maximize)

    # Inventory balance
    def balance_rule(mdl, p, t):
        if t == 0:
            return mdl.produce[p, t] == mdl.sales[p, t] + mdl.inventory[p, t]
        return mdl.inventory[p, t - 1] + mdl.produce[p, t] == mdl.sales[p, t] + mdl.inventory[p, t]
    model.balance = pyo.Constraint(model.P, model.T, rule=balance_rule)

    # Machine capacity constraints
    def grinder_rule(mdl, t):
        return sum(mt_grinder[p] * mdl.produce[p, t] for p in mdl.P) <= grinder_hours[t]
    model.grinder_cap = pyo.Constraint(model.T, rule=grinder_rule)

    def drill_rule(mdl, t):
        return sum(mt_drill[p] * mdl.produce[p, t] for p in mdl.P) <= drill_hours[t]
    model.drill_cap = pyo.Constraint(model.T, rule=drill_rule)

    def borer_rule(mdl, t):
        return sum(mt_borer[p] * mdl.produce[p, t] for p in mdl.P) <= borer_hours[t]
    model.borer_cap = pyo.Constraint(model.T, rule=borer_rule)

    # Inventory capacity
    def inv_cap_rule(mdl, p, t):
        return mdl.inventory[p, t] <= inv_cap
    model.inv_cap = pyo.Constraint(model.P, model.T, rule=inv_cap_rule)

    # Sales limits
    def sales_limit_rule(mdl, p, t):
        return mdl.sales[p, t] <= sales_limit[p][t]
    model.sales_limit = pyo.Constraint(model.P, model.T, rule=sales_limit_rule)

    # Target final inventory
    def final_inv_rule(mdl, p):
        return mdl.inventory[p, T - 1] == target_final[p]
    model.final_inv = pyo.Constraint(model.P, rule=final_inv_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj_expr))
    return {"objective": obj_val, "status": "optimal"}