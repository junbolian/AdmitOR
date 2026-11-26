import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit = [params["profit_per_unit_0"], params["profit_per_unit_1"]]
    hold = params["holding_cost_per_unit"]
    g = [params["grinder_hours_per_unit_0"], params["grinder_hours_per_unit_1"]]
    d = [params["drill_hours_per_unit_0"], params["drill_hours_per_unit_1"]]
    b = [params["borer_hours_per_unit_0"], params["borer_hours_per_unit_1"]]
    gcap = params["grinder_capacity"]
    dcap = params["drill_capacity"]
    bcap = params["borer_capacity"]
    maxinv = params["max_inventory_per_product"]
    maxsales = {
        0: [params["max_sales_product_0"]] * 4,
        1: [params["max_sales_product_1"]] * 4,
    }
    term = params["terminal_inventory_per_product"]

    T = 4
    periods = list(range(T))
    products = [0, 1]

    model = pyo.ConcreteModel()
    model.T = pyo.RangeSet(0, T - 1)
    model.P = pyo.Set(initialize=products)

    model.x = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)
    model.s = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)
    model.inv = pyo.Var(model.P, model.T, within=pyo.NonNegativeReals)

    model.obj = pyo.Objective(
        expr=sum(profit[p] * model.s[p, t] for p in products for t in periods)
        - sum(hold * model.inv[p, t] for p in products for t in periods),
        sense=pyo.maximize,
    )

    def balance_rule(model, p, t):
        if t == 0:
            return model.x[p, t] == model.s[p, t] + model.inv[p, t]
        return model.inv[p, t - 1] + model.x[p, t] == model.s[p, t] + model.inv[p, t]

    model.balance = pyo.Constraint(model.P, model.T, rule=balance_rule)

    model.grinder = pyo.Constraint(
        model.T,
        rule=lambda model, t: sum(g[p] * model.x[p, t] for p in products) <= gcap,
    )
    model.drill = pyo.Constraint(
        model.T,
        rule=lambda model, t: sum(d[p] * model.x[p, t] for p in products) <= dcap,
    )
    model.borer = pyo.Constraint(
        model.T,
        rule=lambda model, t: sum(b[p] * model.x[p, t] for p in products) <= bcap,
    )

    model.invcap = pyo.Constraint(
        model.P, model.T,
        rule=lambda model, p, t: model.inv[p, t] <= maxinv,
    )

    model.sales_lim = pyo.Constraint(
        model.P, model.T,
        rule=lambda model, p, t: model.s[p, t] <= maxsales[p][t],
    )

    model.terminal = pyo.Constraint(
        model.P,
        rule=lambda model, p: model.inv[p, T - 1] == term,
    )

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.obj))
    except Exception:
        return {"objective": None, "status": "infeasible or unbounded"}

    return {"objective": obj_val, "status": "optimal"}