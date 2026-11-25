import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit = params["profit_per_unit"]
    hold = params["holding_cost_per_unit_per_period"]
    mcap = params["machine_capacity"]
    ptime = params["processing_time"]
    maxinv = params["max_inventory"]
    maxsales = params["max_sales"]
    target = params["target_final_inventory"]

    products = list(range(3))
    periods = list(range(4))
    machines = list(range(3))

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=products)
    model.T = pyo.Set(initialize=periods)
    model.M = pyo.Set(initialize=machines)

    model.produce = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)
    model.inventory = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)
    model.sales = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)

    def obj_rule(md):
        revenue = sum(profit[p] * md.sales[p, t] for p in md.P for t in md.T)
        holding = sum(hold * md.inventory[p, t] for p in md.P for t in md.T)
        return revenue - holding

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def balance_first(md, p):
        return md.produce[p, 0] == md.sales[p, 0] + md.inventory[p, 0]

    model.bal_first = pyo.Constraint(model.P, rule=balance_first)

    def balance_later(md, p, t):
        return md.inventory[p, t - 1] + md.produce[p, t] == md.sales[p, t] + md.inventory[p, t]

    model.bal_later = pyo.Constraint(
        model.P,
        model.T,
        rule=lambda md, p, t: pyo.Constraint.Skip if t == 0 else balance_later(md, p, t),
    )

    def cap_rule(md, mch, t):
        return sum(ptime[mch][p] * md.produce[p, t] for p in md.P) <= mcap[mch][t]

    model.cap = pyo.Constraint(model.M, model.T, rule=cap_rule)

    def inv_rule(md, p, t):
        return md.inventory[p, t] <= maxinv

    model.invlim = pyo.Constraint(model.P, model.T, rule=inv_rule)

    def sales_rule(md, p, t):
        return md.sales[p, t] <= maxsales[p][t]

    model.saleslim = pyo.Constraint(model.P, model.T, rule=sales_rule)

    def final_rule(md, p):
        return md.inventory[p, periods[-1]] >= target[p]

    model.finalinv = pyo.Constraint(model.P, rule=final_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}