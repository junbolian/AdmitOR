import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit_per_unit = params["profit_per_unit"]
    holding_cost = params["holding_cost_per_unit_per_period"]
    grinder_hours = params["grinder_hours"]
    drill_hours = params["drill_hours"]
    borer_hours = params["borer_hours"]
    mt_grinder = params["machine_time_grinder"]
    mt_drill = params["machine_time_drill"]
    mt_borer = params["machine_time_borer"]
    inv_capacity = params["inventory_capacity"]
    sales_limit = params["sales_limit"]
    target_final_inv = params["target_final_inventory"]

    products = range(3)
    periods = range(5)

    # Normalize scalar-or-list params to per-product values
    if isinstance(inv_capacity, (int, float)):
        inv_cap_p = {p: inv_capacity for p in products}
    else:
        inv_cap_p = {p: inv_capacity[p] for p in products}

    if isinstance(target_final_inv, (int, float)):
        target_final_p = {p: target_final_inv for p in products}
    else:
        target_final_p = {p: target_final_inv[p] for p in products}

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables
    produce = model.addVars(products, periods, lb=0.0, name="produce")
    inventory = model.addVars(products, periods, lb=0.0, name="inventory")
    sell = model.addVars(products, periods, lb=0.0, name="sell")

    # Objective: maximize revenue minus holding costs
    model.setObjective(
        gp.quicksum(profit_per_unit[p] * sell[p, t] for p in products for t in periods)
        - gp.quicksum(holding_cost * inventory[p, t] for p in products for t in periods),
        GRB.MAXIMIZE
    )

    # Inventory balance constraints
    for p in products:
        model.addConstr(
            produce[p, 0] == sell[p, 0] + inventory[p, 0],
            name=f"balance_p{p}_t0"
        )
        for t in range(1, 5):
            model.addConstr(
                inventory[p, t - 1] + produce[p, t] == sell[p, t] + inventory[p, t],
                name=f"balance_p{p}_t{t}"
            )

    # Machine capacity constraints
    for t in periods:
        model.addConstr(
            gp.quicksum(mt_grinder[p] * produce[p, t] for p in products) <= grinder_hours[t],
            name=f"grinder_t{t}"
        )
        model.addConstr(
            gp.quicksum(mt_drill[p] * produce[p, t] for p in products) <= drill_hours[t],
            name=f"drill_t{t}"
        )
        model.addConstr(
            gp.quicksum(mt_borer[p] * produce[p, t] for p in products) <= borer_hours[t],
            name=f"borer_t{t}"
        )

    # Inventory capacity constraints
    for p in products:
        for t in periods:
            model.addConstr(
                inventory[p, t] <= inv_cap_p[p],
                name=f"inv_cap_p{p}_t{t}"
            )

    # Sales limit constraints
    for p in products:
        for t in periods:
            row = sales_limit[p] if isinstance(sales_limit, (list, tuple)) else sales_limit
            limit = row[t] if isinstance(row, (list, tuple)) else row
            model.addConstr(
                sell[p, t] <= limit,
                name=f"sales_limit_p{p}_t{t}"
            )

    # Target final inventory constraints
    for p in products:
        model.addConstr(
            inventory[p, 4] == target_final_p[p],
            name=f"final_inv_p{p}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}