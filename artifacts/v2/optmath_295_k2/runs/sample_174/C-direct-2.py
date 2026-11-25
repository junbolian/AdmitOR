import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit_per_unit = params["profit_per_unit"]
    holding_cost = params["holding_cost"]
    machine_hours_per_unit = params["machine_hours_per_unit"]
    grinder_capacity = params["grinder_capacity"]
    drill_capacity = params["drill_capacity"]
    borer_capacity = params["borer_capacity"]
    inventory_limit = params["inventory_limit"]
    sales_limit_product0 = params["sales_limit_product0"]
    sales_limit_product1 = params["sales_limit_product1"]
    target_inventory = params["target_inventory"]

    num_products = 2
    num_periods = 4
    products = range(num_products)
    periods = range(num_periods)

    # Normalize holding_cost: if scalar, expand to per-product list
    if hasattr(holding_cost, '__len__'):
        hc = [holding_cost[p] for p in products]
    else:
        hc = [float(holding_cost)] * num_products

    model = gp.Model("factory_production")
    model.setParam("OutputFlag", 0)

    produce = model.addVars(num_products, num_periods, lb=0, name="produce")
    inventory = model.addVars(num_products, num_periods, lb=0, name="inventory")
    sell = model.addVars(num_products, num_periods, lb=0, name="sell")

    model.setObjective(
        gp.quicksum(profit_per_unit[p] * sell[p, t] for p in products for t in periods)
        - gp.quicksum(hc[p] * inventory[p, t] for p in products for t in periods),
        GRB.MAXIMIZE
    )

    # Initial balance (Period 0)
    for p in products:
        model.addConstr(
            produce[p, 0] == sell[p, 0] + inventory[p, 0],
            name=f"initial_balance_p{p}"
        )

    # Inventory balance for periods 1-3
    for p in products:
        for t in range(1, num_periods):
            model.addConstr(
                inventory[p, t - 1] + produce[p, t] == sell[p, t] + inventory[p, t],
                name=f"inv_balance_p{p}_t{t}"
            )

    # Grinder capacity
    for t in periods:
        model.addConstr(
            gp.quicksum(machine_hours_per_unit["grinders"][p] * produce[p, t] for p in products)
            <= grinder_capacity[t],
            name=f"grinder_cap_t{t}"
        )

    # Drill capacity
    for t in periods:
        model.addConstr(
            gp.quicksum(machine_hours_per_unit["drills"][p] * produce[p, t] for p in products)
            <= drill_capacity[t],
            name=f"drill_cap_t{t}"
        )

    # Borer capacity
    for t in periods:
        model.addConstr(
            gp.quicksum(machine_hours_per_unit["borers"][p] * produce[p, t] for p in products)
            <= borer_capacity[t],
            name=f"borer_cap_t{t}"
        )

    # Inventory limits
    for p in products:
        for t in periods:
            model.addConstr(
                inventory[p, t] <= inventory_limit,
                name=f"inv_limit_p{p}_t{t}"
            )

    # Sales limits
    for t in periods:
        model.addConstr(sell[0, t] <= sales_limit_product0[t], name=f"sales_limit_p0_t{t}")
        model.addConstr(sell[1, t] <= sales_limit_product1[t], name=f"sales_limit_p1_t{t}")

    # Target inventory at end of horizon
    for p in products:
        model.addConstr(
            inventory[p, num_periods - 1] == target_inventory[p],
            name=f"target_inv_p{p}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}