import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit = params["profit_per_unit"]
    hold_cost = params["holding_cost_per_unit_per_period"]
    grinder_hrs = params["grinder_hours_per_unit"]
    drill_hrs = params["drill_hours_per_unit"]
    borer_hrs = params["borer_hours_per_unit"]
    grinder_cap = params["grinder_capacity_per_period"]
    drill_cap = params["drill_capacity_per_period"]
    borer_cap = params["borer_capacity_per_period"]
    max_inv = params["max_inventory_per_product"]
    max_sales = params["max_sales"]
    final_inv = params["final_inventory_target"]

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=[0, 1, 2])
    model.T = pyo.Set(initialize=[0, 1, 2, 3, 4, 5])

    model.produce = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)
    model.inventory = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)
    model.sell = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)

    model.inv_cap = pyo.Constraint(
        model.P, model.T, rule=lambda mm, p, t: mm.inventory[p, t] <= max_inv[p]
    )

    model.sales_lim = pyo.Constraint(
        model.P, model.T, rule=lambda mm, p, t: mm.sell[p, t] <= max_sales[p][t]
    )

    model.balance0 = pyo.Constraint(
        model.P,
        rule=lambda mm, p: mm.produce[p, 0] == mm.sell[p, 0] + mm.inventory[p, 0],
    )

    def bal_rule(mm, p, t):
        if t == 0:
            return pyo.Constraint.Skip
        return mm.inventory[p, t - 1] + mm.produce[p, t] == mm.sell[p, t] + mm.inventory[p, t]

    model.balance = pyo.Constraint(model.P, model.T, rule=bal_rule)

    model.final_target = pyo.Constraint(
        model.P, rule=lambda mm, p: mm.inventory[p, 5] == final_inv[p]
    )

    def grinder_rule(mm, t):
        return sum(grinder_hrs[p] * mm.produce[p, t] for p in mm.P) <= grinder_cap[t]

    def drill_rule(mm, t):
        return sum(drill_hrs[p] * mm.produce[p, t] for p in mm.P) <= drill_cap[t]

    def borer_rule(mm, t):
        return sum(borer_hrs[p] * mm.produce[p, t] for p in mm.P) <= borer_cap[t]

    model.grinder_limit = pyo.Constraint(model.T, rule=grinder_rule)
    model.drill_limit = pyo.Constraint(model.T, rule=drill_rule)
    model.borer_limit = pyo.Constraint(model.T, rule=borer_rule)

    def obj_rule(mm):
        revenue = sum(profit[p] * mm.sell[p, t] for p in mm.P for t in mm.T)
        holding = sum(hold_cost * mm.inventory[p, t] for p in mm.P for t in mm.T)
        return revenue - holding

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}