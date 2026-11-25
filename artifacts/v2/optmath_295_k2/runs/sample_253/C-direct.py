import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit_per_unit = params["profit_per_unit"]
    holding_cost = params["holding_cost"]
    grinder_capacity = params["grinder_capacity"]
    drill_capacity = params["drill_capacity"]
    borer_capacity = params["borer_capacity"]
    grinder_hours_per_unit = params["grinder_hours_per_unit"]
    drill_hours_per_unit = params["drill_hours_per_unit"]
    borer_hours_per_unit = params["borer_hours_per_unit"]
    inventory_limit = params["inventory_limit"]
    sales_limit_product0 = params["sales_limit_product0"]
    sales_limit_product1 = params["sales_limit_product1"]
    target_inventory_raw = params["target_inventory"]

    # Normalize target_inventory to a list indexed by product
    try:
        target_inventory = [target_inventory_raw[0], target_inventory_raw[1]]
    except (TypeError, KeyError):
        target_inventory = [target_inventory_raw, target_inventory_raw]

    products = [0, 1]
    periods = [0, 1, 2, 3]

    model = gp.Model("factory_planning")
    model.setParam("OutputFlag", 0)

    # Decision variables
    produce = model.addVars(products, periods, lb=0.0, name="produce")
    inventory = model.addVars(products, periods, lb=0.0, name="inventory")
    sales = model.addVars(products, periods, lb=0.0, name="sales")

    # Objective: maximize profit from sales minus holding costs
    model.setObjective(
        gp.quicksum(profit_per_unit[p] * sales[p, t] for p in products for t in periods)
        - gp.quicksum(holding_cost * inventory[p, t] for p in products for t in periods),
        GRB.MAXIMIZE
    )

    # Initial balance (period 0): production = sales + inventory
    for p in products:
        model.addConstr(
            produce[p, 0] == sales[p, 0] + inventory[p, 0],
            name=f"init_balance_p{p}"
        )

    # Inventory balance for periods 1-3
    for p in products:
        for t in periods[1:]:
            model.addConstr(
                inventory[p, t - 1] + produce[p, t] == sales[p, t] + inventory[p, t],
                name=f"inv_balance_p{p}_t{t}"
            )

    # Machine capacity constraints
    for t in periods:
        model.addConstr(
            gp.quicksum(grinder_hours_per_unit[p] * produce[p, t] for p in products) <= grinder_capacity,
            name=f"grinder_t{t}"
        )
        model.addConstr(
            gp.quicksum(drill_hours_per_unit[p] * produce[p, t] for p in products) <= drill_capacity,
            name=f"drill_t{t}"
        )
        model.addConstr(
            gp.quicksum(borer_hours_per_unit[p] * produce[p, t] for p in products) <= borer_capacity,
            name=f"borer_t{t}"
        )

    # Inventory limits
    for p in products:
        for t in periods:
            model.addConstr(inventory[p, t] <= inventory_limit, name=f"inv_limit_p{p}_t{t}")

    # Sales limits
    for t in periods:
        model.addConstr(sales[0, t] <= sales_limit_product0[t], name=f"sales_limit_p0_t{t}")
        model.addConstr(sales[1, t] <= sales_limit_product1[t], name=f"sales_limit_p1_t{t}")

    # Target inventory at end of period 3
    for p in products:
        model.addConstr(inventory[p, 3] == target_inventory[p], name=f"target_inv_p{p}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}