import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    profit = params["profit_per_unit"]
    hold_cost = params["holding_cost_per_unit"]
    grinder_h = params["grinder_hours_per_unit"]
    drill_h = params["drill_hours_per_unit"]
    borer_h = params["borer_hours_per_unit"]
    grinder_cap = params["grinder_capacity_per_period"]
    drill_cap = params["drill_capacity_per_period"]
    borer_cap = params["borer_capacity_per_period"]
    inv_cap = params["max_inventory_per_product"]
    max0 = params["max_sales_product_0"]
    max1 = params["max_sales_product_1"]
    max2 = params["max_sales_product_2"]
    term_target = params["terminal_inventory_target"]

    periods = list(range(6))
    products = list(range(3))
    sales_max = {0: max0, 1: max1, 2: max2}
    drill_avail = {t: (0 if t == 2 else drill_cap) for t in periods}

    model = pyo.ConcreteModel()

    model.T = pyo.Set(initialize=periods)
    model.P = pyo.Set(initialize=products)

    model.produce = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)
    model.inventory = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)
    model.sell = pyo.Var(model.P, model.T, domain=pyo.NonNegativeReals)

    model.obj = pyo.Objective(
        expr=sum(profit[p] * model.sell[p, t] for p in products for t in periods)
        - sum(hold_cost * model.inventory[p, t] for p in products for t in periods),
        sense=pyo.maximize,
    )

    # Inventory capacity
    model.inv_cap_con = pyo.Constraint(
        model.P, model.T, rule=lambda m, p, t: m.inventory[p, t] <= inv_cap
    )

    # Sales limits
    model.sales_con = pyo.Constraint(
        model.P,
        model.T,
        rule=lambda m, p, t: m.sell[p, t] <= sales_max[p][t],
    )

    # Flow balance: period 0 (no incoming inventory)
    model.balance0 = pyo.Constraint(
        model.P,
        rule=lambda m, p: m.produce[p, 0] == m.sell[p, 0] + m.inventory[p, 0],
    )

    # Flow balance: subsequent periods
    model.balance = pyo.Constraint(
        model.P,
        pyo.Set(initialize=periods[1:]),
        rule=lambda m, p, t: m.inventory[p, t - 1] + m.produce[p, t]
        == m.sell[p, t] + m.inventory[p, t],
    )

    # Terminal inventory
    model.terminal = pyo.Constraint(
        model.P, rule=lambda m, p: m.inventory[p, 5] == term_target
    )

    # Grinder capacity
    model.grinder_con = pyo.Constraint(
        model.T,
        rule=lambda m, t: sum(grinder_h[p] * m.produce[p, t] for p in products)
        <= grinder_cap,
    )

    # Drill capacity
    model.drill_con = pyo.Constraint(
        model.T,
        rule=lambda m, t: sum(drill_h[p] * m.produce[p, t] for p in products)
        <= drill_avail[t],
    )

    # Borer capacity
    model.borer_con = pyo.Constraint(
        model.T,
        rule=lambda m, t: sum(borer_h[p] * m.produce[p, t] for p in products)
        <= borer_cap,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}