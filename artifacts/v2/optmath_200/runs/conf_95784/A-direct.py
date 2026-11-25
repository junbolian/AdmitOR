import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit = {0: params["profit0"], 1: params["profit1"]}
    hold_cost = {0: params["hold_cost0"], 1: params["hold_cost1"]}
    inv_cap = params["inv_cap"]
    sales_max = {
        0: [params["sales_max0"], params["sales_max0"], params["sales_max0"], params["sales_max0"]],
        1: [params["sales_max1"], params["sales_max1"], params["sales_max1"], params["sales_max1"]],
    }
    grinder_hours = {0: params["grinder_hours0"], 1: params["grinder_hours1"]}
    drill_hours = {0: params["drill_hours0"], 1: params["drill_hours1"]}
    borer_hours = {0: params["borer_hours0"], 1: params["borer_hours1"]}
    grinder_cap = [params["grinder_cap"], params["grinder_cap"], params["grinder_cap"], 0]
    drill_cap = [params["drill_cap"], params["drill_cap"], params["drill_cap"], params["drill_cap"]]
    borer_cap = [params["borer_cap"], params["borer_cap"], params["borer_cap"], params["borer_cap"]]
    final_inv_target = params["final_inv_target"]

    periods = range(4)
    products = [0, 1]

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=products)
    model.T = pyo.Set(initialize=list(periods))

    model.prod = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)
    model.sales = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)
    model.inv = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)

    # Inventory balance
    def balance_rule(mdl, p, t):
        if t == 0:
            return mdl.prod[p, t] == mdl.sales[p, t] + mdl.inv[p, t]
        return mdl.inv[p, t - 1] + mdl.prod[p, t] == mdl.sales[p, t] + mdl.inv[p, t]

    model.balance_con = pyo.Constraint(model.P, model.T, rule=balance_rule)

    # Inventory capacity
    def inv_cap_rule(mdl, p, t):
        return mdl.inv[p, t] <= inv_cap

    model.inv_cap_con = pyo.Constraint(model.P, model.T, rule=inv_cap_rule)

    # Sales limits
    def sales_rule(mdl, p, t):
        return mdl.sales[p, t] <= sales_max[p][t]

    model.sales_con = pyo.Constraint(model.P, model.T, rule=sales_rule)

    # Final inventory target
    def final_inv_rule(mdl, p):
        return mdl.inv[p, 3] == final_inv_target

    model.final_inv_con = pyo.Constraint(model.P, rule=final_inv_rule)

    # Grinder capacity
    def grinder_rule(mdl, t):
        return sum(grinder_hours[p] * mdl.prod[p, t] for p in products) <= grinder_cap[t]

    model.grinder_con = pyo.Constraint(model.T, rule=grinder_rule)

    # Drill capacity
    def drill_rule(mdl, t):
        return sum(drill_hours[p] * mdl.prod[p, t] for p in products) <= drill_cap[t]

    model.drill_con = pyo.Constraint(model.T, rule=drill_rule)

    # Borer capacity
    def borer_rule(mdl, t):
        return sum(borer_hours[p] * mdl.prod[p, t] for p in products) <= borer_cap[t]

    model.borer_con = pyo.Constraint(model.T, rule=borer_rule)

    def obj_rule(mdl):
        revenue = sum(profit[p] * mdl.sales[p, t] for p in products for t in periods)
        holding = sum(hold_cost[p] * mdl.inv[p, t] for p in products for t in periods)
        return revenue - holding

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
    except Exception:
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}