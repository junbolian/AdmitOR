import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    reservations = params["reservations"]
    ending_inventory_required = params["ending_inventory_required"]
    production_hours_per_quarter = params["production_hours_per_quarter"]
    hours_per_unit = params["hours_per_unit"]
    delay_penalty = params["delay_penalty"]
    inventory_cost = params["inventory_cost"]

    products = [0, 1, 2]
    quarters = [0, 1, 2, 3]
    forbidden = {(0, 1)}

    demand = {(i, t): reservations[i][t] for i in products for t in quarters}
    hpu = {i: hours_per_unit[i] for i in products}
    delay_cost = {i: delay_penalty[i] for i in products}
    end_req = {i: ending_inventory_required[i] for i in products}

    model = pyo.ConcreteModel()

    model.x = pyo.Var(products, quarters, within=pyo.NonNegativeReals)
    model.inv = pyo.Var(products, quarters, within=pyo.NonNegativeReals)
    model.short = pyo.Var(products, quarters, within=pyo.NonNegativeReals)
    model.delivered = pyo.Var(products, quarters, within=pyo.NonNegativeReals)

    for (i, t) in forbidden:
        model.x[i, t].fix(0)

    model.cap = pyo.Constraint(
        quarters,
        rule=lambda m, t: sum(hpu[i] * m.x[i, t] for i in products)
        <= production_hours_per_quarter,
    )

    def inv_flow(m, i, t):
        prev_inv = 0 if t == 0 else m.inv[i, t - 1]
        return m.inv[i, t] == m.x[i, t] + prev_inv - m.delivered[i, t]

    model.inv_flow = pyo.Constraint(products, quarters, rule=inv_flow)

    model.deliver_def = pyo.Constraint(
        products,
        quarters,
        rule=lambda m, i, t: m.delivered[i, t] + m.short[i, t] == demand[i, t],
    )

    def deliver_limit(m, i, t):
        prev_inv = 0 if t == 0 else m.inv[i, t - 1]
        return m.delivered[i, t] <= m.x[i, t] + prev_inv

    model.deliver_limit = pyo.Constraint(products, quarters, rule=deliver_limit)

    model.endstock = pyo.Constraint(
        products, rule=lambda m, i: m.inv[i, 3] >= end_req[i]
    )

    model.obj = pyo.Objective(
        expr=sum(delay_cost[i] * model.short[i, t] for i in products for t in quarters)
        + sum(inventory_cost * model.inv[i, t] for i in products for t in quarters),
        sense=pyo.minimize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}