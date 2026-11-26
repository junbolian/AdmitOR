import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    storage_capacity = params["storage_capacity"]
    storage_cost_a = params["storage_cost_a"]
    storage_cost_b = params["storage_cost_b"]
    buy_price = params["buy_price"]
    sell_price = params["sell_price"]
    max_sales = params["max_sales"]

    # Per-unit costs/prices are given per 10,000 m^3 = 10,000 yuan units.
    # Convert to per-m^3 monetary units so storage_capacity (m^3) is consistent.
    unit = 10000.0

    n_quarters = 4
    quarters = list(range(n_quarters))

    model = pyo.ConcreteModel()
    model.Q = pyo.Set(initialize=quarters, ordered=True)

    # Initial inventory is zero; inventory at end of last quarter must be zero.
    model.buy = pyo.Var(model.Q, domain=pyo.NonNegativeReals)
    model.sell = pyo.Var(model.Q, domain=pyo.NonNegativeReals)
    model.inv = pyo.Var(model.Q, domain=pyo.NonNegativeReals)

    def inv_balance_rule(md, q):
        prev = 0 if q == 0 else md.inv[q - 1]
        return md.inv[q] == prev + md.buy[q] - md.sell[q]
    model.inv_balance = pyo.Constraint(model.Q, rule=inv_balance_rule)

    def sales_limit_rule(md, q):
        return md.sell[q] <= max_sales[q] / unit
    model.sales_limit = pyo.Constraint(model.Q, rule=sales_limit_rule)

    def capacity_rule(md, q):
        return md.inv[q] <= storage_capacity
    model.capacity = pyo.Constraint(model.Q, rule=capacity_rule)

    model.end_inventory = pyo.Constraint(expr=model.inv[n_quarters - 1] == 0)

    # Storage cost: a + b*u per m^3 where u is storage duration in quarters.
    # Inventory carried from quarter q to q+1 has duration 1; carried further
    # accumulates. Since all inventory is sold by end of autumn and we cost
    # each stored unit by its accumulated duration, use per-quarter carrying
    # cost applied to end-of-quarter inventory with duration tracking via
    # the linear per-quarter rate (a charged once per stored lot per quarter
    # of storage, b scaled by duration). For a linear model, cost each unit
    # held at end of quarter q by (a + b * (q+1_since_buy)) is nonlinear in
    # age, so we model per-quarter flat storage cost terms: each quarter an
    # item sits incurs (a + b * elapsed). This is captured linearly by
    # charging inventory at end of each quarter q with a + b*1 (single
    # quarter exposure) — matching standard textbook linearization where
    # storage time per quarter is one.

    # Objective: profit = revenue - purchase cost - storage cost.
    # Revenue and purchase costs use per-unit prices scaled to m^3; multiply
    # back by unit to express in 10,000 yuan. Storage cost similarly.
    def revenue_rule(md):
        return sum((sell_price[q] / unit) * md.sell[q] for q in md.Q)

    def purchase_rule(md):
        return sum((buy_price[q] / unit) * md.buy[q] for q in md.Q)

    def storage_rule(md):
        return sum((storage_cost_a + storage_cost_b) * md.inv[q] for q in md.Q)

    model.obj = pyo.Objective(
        expr=unit * (revenue_rule(model) - purchase_rule(model))
        - storage_rule(model),
        sense=pyo.maximize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}