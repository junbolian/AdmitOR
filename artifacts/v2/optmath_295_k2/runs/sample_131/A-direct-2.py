import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    T = list(range(4))
    P = list(range(3))

    profit = [
        params["profit_product_0"],
        params["profit_product_1"],
        params["profit_product_2"],
    ]
    holding_cost = params["holding_cost"]

    grinder_cap = params["grinder_capacity"]
    drill_cap = params["drill_capacity"]
    borer_cap = params["borer_capacity"]

    max_inv = params["max_inventory"]

    max_sales = {
        (t, p): params["max_sales_period_%d_product_%d" % (t, p)]
        for t in T
        for p in P
    }

    final_inv_target = params["final_inventory_target"]

    time_grinder = [
        params["time_grinder_product_0"],
        params["time_grinder_product_1"],
        params["time_grinder_product_2"],
    ]
    time_drill = [
        params["time_drill_product_0"],
        params["time_drill_product_1"],
        params["time_drill_product_2"],
    ]
    time_borer = [
        params["time_borer_product_0"],
        params["time_borer_product_1"],
        params["time_borer_product_2"],
    ]

    model = pyo.ConcreteModel()

    model.T = pyo.Set(initialize=T, ordered=True)
    model.P = pyo.Set(initialize=P, ordered=True)

    model.produce = pyo.Var(model.T, model.P, domain=pyo.NonNegativeReals)
    model.inventory = pyo.Var(model.T, model.P, domain=pyo.NonNegativeReals)
    model.sales = pyo.Var(model.T, model.P, domain=pyo.NonNegativeReals)

    def inventory_balance_rule(mdl, t, p):
        if t == 0:
            return mdl.produce[t, p] == mdl.sales[t, p] + mdl.inventory[t, p]
        return (
            mdl.inventory[t - 1, p] + mdl.produce[t, p]
            == mdl.sales[t, p] + mdl.inventory[t, p]
        )

    model.balance_con = pyo.Constraint(model.T, model.P, rule=inventory_balance_rule)

    def grinder_cap_rule(mdl, t):
        expr = sum(time_grinder[p] * mdl.produce[t, p] for p in P)
        return pyo.Constraint.Expression(expr <= grinder_cap) if False else (expr <= grinder_cap)

    def grinder_rule(mdl, t):
        return sum(time_grinder[p] * mdl.produce[t, p] for p in P) <= grinder_cap

    model.grinder_con = pyo.Constraint(model.T, rule=grinder_rule)

    def drill_rule(mdl, t):
        return sum(time_drill[p] * mdl.produce[t, p] for p in P) <= drill_cap

    model.drill_con = pyo.Constraint(model.T, rule=drill_rule)

    def borer_rule(mdl, t):
        return sum(time_borer[p] * mdl.produce[t, p] for p in P) <= borer_cap

    model.borer_con = pyo.Constraint(model.T, rule=borer_rule)

    def max_inventory_rule(mdl, t, p):
        return mdl.inventory[t, p] <= max_inv

    model.max_inv_con = pyo.Constraint(model.T, model.P, rule=max_inventory_rule)

    def max_sales_rule(mdl, t, p):
        return mdl.sales[t, p] <= max_sales[(t, p)]

    model.max_sales_con = pyo.Constraint(model.T, model.P, rule=max_sales_rule)

    def final_inventory_rule(mdl, p):
        return mdl.inventory[3, p] == final_inv_target

    model.final_inv_con = pyo.Constraint(model.P, rule=final_inventory_rule)

    def objective_rule(mdl):
        revenue = sum(profit[p] * mdl.sales[t, p] for t in T for p in P)
        holding = sum(holding_cost * mdl.inventory[t, p] for t in T for p in P)
        return revenue - holding

    model.obj = pyo.Objective(rule=objective_rule, sense=pyo.maximize)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
        return {"objective": obj_val, "status": "optimal"}
    except Exception:
        return {"objective": None, "status": "infeasible_or_failed"}