import gurobipy as gp
from gurobipy import GRB


def solve(params):
    products = [0, 1]
    periods = [0, 1, 2, 3]

    profit = {0: params["profit_per_unit_product0"], 1: params["profit_per_unit_product1"]}
    holding_cost = params["holding_cost_per_unit_per_period"]

    grinder_hours = {0: params["grinder_hours_product0"], 1: params["grinder_hours_product1"]}
    grinder_cap = params["grinder_capacity_per_period"]

    drill_hours = {0: params["drill_hours_product0"], 1: params["drill_hours_product1"]}
    drill_cap = params["drill_capacity_per_period"]

    borer_hours = {0: params["borer_hours_product0"], 1: params["borer_hours_product1"]}
    borer_cap = params["borer_capacity_per_period"]

    max_inv = {0: params["max_inventory_product0"], 1: params["max_inventory_product1"]}

    sales_limit = {0: params["sales_limit_product0"], 1: params["sales_limit_product1"]}

    target_inv = {0: params["target_inventory_product0"], 1: params["target_inventory_product1"]}

    model = gp.Model("factory_production")
    model.Params.OutputFlag = 0

    P = model.addVars(products, periods, lb=0.0, name="P")
    I = model.addVars(products, periods, lb=0.0, name="I")
    S = model.addVars(products, periods, lb=0.0, name="S")

    model.setObjective(
        gp.quicksum(profit[p] * S[p, t] for p in products for t in periods)
        - holding_cost * gp.quicksum(I[p, t] for p in products for t in periods),
        GRB.MAXIMIZE,
    )

    # Initial balance: production in period 0 equals sales plus end inventory
    for p in products:
        model.addConstr(P[p, 0] == S[p, 0] + I[p, 0], name=f"init_bal_{p}")

    # Inventory balance for periods 1..3
    for p in products:
        for t in periods[1:]:
            model.addConstr(I[p, t - 1] + P[p, t] == S[p, t] + I[p, t], name=f"inv_bal_{p}_{t}")

    # Machine capacity per period
    for t in periods:
        model.addConstr(
            gp.quicksum(grinder_hours[p] * P[p, t] for p in products) <= grinder_cap,
            name=f"grinder_cap_{t}",
        )
        model.addConstr(
            gp.quicksum(drill_hours[p] * P[p, t] for p in products) <= drill_cap,
            name=f"drill_cap_{t}",
        )
        model.addConstr(
            gp.quicksum(borer_hours[p] * P[p, t] for p in products) <= borer_cap,
            name=f"borer_cap_{t}",
        )

    # Inventory upper bounds
    for p in products:
        for t in periods:
            model.addConstr(I[p, t] <= max_inv[p], name=f"max_inv_{p}_{t}")

    # Sales upper bounds (period-indexed lists)
    for p in products:
        for t in periods:
            model.addConstr(S[p, t] <= sales_limit[p][t], name=f"sales_lim_{p}_{t}")

    # Terminal inventory targets
    for p in products:
        model.addConstr(I[p, 3] == target_inv[p], name=f"target_inv_{p}")

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    return {"objective": None, "status": f"status_{model.status}"}