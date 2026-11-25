import gurobipy as gp
from gurobipy import GRB


def solve(params):
    profit = [params["profit_per_unit_product0"], params["profit_per_unit_product1"]]
    holding_cost = params["holding_cost_per_unit_per_period"]
    grinder_cap = params["grinder_capacity_per_period"]
    drill_cap = params["drill_capacity_per_period"]
    borer_cap = params["borer_capacity_per_period"]
    grinder_hours = [params["grinder_hours_product0"], params["grinder_hours_product1"]]
    drill_hours = [params["drill_hours_product0"], params["drill_hours_product1"]]
    borer_hours = [params["borer_hours_product0"], params["borer_hours_product1"]]
    max_inv = params["max_inventory_per_product_per_period"]
    max_sales = [
        params["max_sales_product0_per_period"],
        params["max_sales_product1_per_period"],
    ]
    terminal_inv = [
        params["terminal_inventory_product0"],
        params["terminal_inventory_product1"],
    ]

    products = [0, 1]
    periods = [0, 1, 2, 3]

    model = gp.Model("production_planning")
    model.setParam("OutputFlag", 0)

    prod = model.addVars(products, periods, name="prod")
    sell = model.addVars(products, periods, name="sell")
    inv = model.addVars(products, periods, name="inv")

    model.setObjective(
        gp.quicksum(profit[p] * sell[p, t] for p in products for t in periods)
        - holding_cost
        * gp.quicksum(inv[p, t] for p in products for t in periods),
        GRB.MAXIMIZE,
    )

    # Inventory balance: period 0 has no initial inventory.
    for p in products:
        model.addConstr(prod[p, 0] == sell[p, 0] + inv[p, 0])
        for t in periods[1:]:
            model.addConstr(inv[p, t - 1] + prod[p, t] == sell[p, t] + inv[p, t])

    # Machine capacity per period.
    for t in periods:
        model.addConstr(
            gp.quicksum(grinder_hours[p] * prod[p, t] for p in products)
            <= grinder_cap[t]
        )
        model.addConstr(
            gp.quicksum(drill_hours[p] * prod[p, t] for p in products) <= drill_cap[t]
        )
        model.addConstr(
            gp.quicksum(borer_hours[p] * prod[p, t] for p in products) <= borer_cap[t]
        )

    # Inventory and sales bounds.
    for p in products:
        for t in periods:
            model.addConstr(inv[p, t] <= max_inv)
            model.addConstr(sell[p, t] <= max_sales[p][t])

    # Terminal inventory requirement at end of last period.
    for p in products:
        model.addConstr(inv[p, periods[-1]] == terminal_inv[p])

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    return {"objective": None, "status": "failed"}