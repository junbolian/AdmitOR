import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit_per_unit = params["profit_per_unit"]
    holding_cost_per_unit = params["holding_cost_per_unit"]
    grinder_time = params["grinder_time"]
    drill_time = params["drill_time"]
    borer_time = params["borer_time"]
    grinder_capacity = params["grinder_capacity"]
    drill_capacity = params["drill_capacity"]
    borer_capacity = params["borer_capacity"]
    max_inventory = params["max_inventory"]
    max_sales = params["max_sales"]
    final_inventory = params["final_inventory"]

    num_products = 3
    num_periods = 6
    products = range(num_products)
    periods = range(num_periods)

    # Normalize final_inventory: if scalar, expand to list; otherwise keep as-is
    if isinstance(final_inventory, (int, float)):
        final_inv_list = [final_inventory] * num_products
    else:
        final_inv_list = list(final_inventory)

    model = gp.Model("production_planning")
    model.setParam("OutputFlag", 0)

    # Decision variables
    produce = model.addVars(num_products, num_periods, lb=0.0, name="produce")
    sell = model.addVars(num_products, num_periods, lb=0.0, name="sell")
    inventory = model.addVars(num_products, num_periods, lb=0.0, name="inventory")

    # Objective: maximize profit from sales minus holding costs
    model.setObjective(
        gp.quicksum(profit_per_unit[p] * sell[p, t] for p in products for t in periods)
        - gp.quicksum(holding_cost_per_unit * inventory[p, t] for p in products for t in periods),
        GRB.MAXIMIZE
    )

    # Inventory balance constraints
    for p in products:
        for t in periods:
            if t == 0:
                model.addConstr(
                    produce[p, t] == sell[p, t] + inventory[p, t],
                    name=f"balance_{p}_{t}"
                )
            else:
                model.addConstr(
                    inventory[p, t-1] + produce[p, t] == sell[p, t] + inventory[p, t],
                    name=f"balance_{p}_{t}"
                )

    # Machine capacity constraints
    for t in periods:
        model.addConstr(
            gp.quicksum(grinder_time[p] * produce[p, t] for p in products) <= grinder_capacity[t],
            name=f"grinder_{t}"
        )
        model.addConstr(
            gp.quicksum(drill_time[p] * produce[p, t] for p in products) <= drill_capacity[t],
            name=f"drill_{t}"
        )
        model.addConstr(
            gp.quicksum(borer_time[p] * produce[p, t] for p in products) <= borer_capacity[t],
            name=f"borer_{t}"
        )

    # Maximum inventory constraints
    for p in products:
        for t in periods:
            model.addConstr(inventory[p, t] <= max_inventory, name=f"max_inv_{p}_{t}")

    # Maximum sales constraints
    for p in products:
        for t in periods:
            model.addConstr(sell[p, t] <= max_sales[p][t], name=f"max_sales_{p}_{t}")

    # Final inventory requirement
    for p in products:
        model.addConstr(
            inventory[p, num_periods - 1] == final_inv_list[p],
            name=f"final_inv_{p}"
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