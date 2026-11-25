import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit_per_unit = params["profit_per_unit"]
    holding_cost = params["holding_cost_per_unit_per_period"]
    grinder_hours = params["grinder_hours_per_unit"]
    drill_hours = params["drill_hours_per_unit"]
    borer_hours = params["borer_hours_per_unit"]
    grinder_cap = params["grinder_capacity_per_period"]
    drill_cap = params["drill_capacity_per_period"]
    borer_cap = params["borer_capacity_per_period"]
    max_inv = params["max_inventory_per_product"]
    max_sales = params["max_sales"]
    final_inv_target = params["final_inventory_target"]

    num_products = 3
    num_periods = 6
    products = range(num_products)
    periods = range(num_periods)

    model = gp.Model("manufacturing")
    model.setParam("OutputFlag", 0)

    # Decision variables
    produce = model.addVars(num_products, num_periods, lb=0.0, name="produce")
    inventory = model.addVars(num_products, num_periods, lb=0.0, name="inventory")
    sell = model.addVars(num_products, num_periods, lb=0.0, name="sell")

    # Objective: maximize profit from sales minus holding costs
    model.setObjective(
        gp.quicksum(profit_per_unit[p] * sell[p, t] for p in products for t in periods)
        - gp.quicksum(holding_cost * inventory[p, t] for p in products for t in periods),
        GRB.MAXIMIZE
    )

    # Inventory balance constraints
    for p in products:
        for t in periods:
            if t == 0:
                model.addConstr(
                    produce[p, t] == sell[p, t] + inventory[p, t],
                    name=f"balance_p{p}_t{t}"
                )
            else:
                model.addConstr(
                    inventory[p, t - 1] + produce[p, t] == sell[p, t] + inventory[p, t],
                    name=f"balance_p{p}_t{t}"
                )

    # Grinder capacity constraints
    for t in periods:
        model.addConstr(
            gp.quicksum(grinder_hours[p] * produce[p, t] for p in products) <= grinder_cap[t],
            name=f"grinder_t{t}"
        )

    # Drill capacity constraints
    for t in periods:
        model.addConstr(
            gp.quicksum(drill_hours[p] * produce[p, t] for p in products) <= drill_cap[t],
            name=f"drill_t{t}"
        )

    # Borer capacity constraints
    for t in periods:
        model.addConstr(
            gp.quicksum(borer_hours[p] * produce[p, t] for p in products) <= borer_cap[t],
            name=f"borer_t{t}"
        )

    # Maximum inventory constraints
    # max_inv may be a scalar or a per-product list; handle both cases
    for p in products:
        for t in periods:
            try:
                cap = max_inv[p]
            except (TypeError, KeyError):
                cap = max_inv
            model.addConstr(
                inventory[p, t] <= cap,
                name=f"max_inv_p{p}_t{t}"
            )

    # Maximum sales constraints
    for p in products:
        for t in periods:
            model.addConstr(
                sell[p, t] <= max_sales[p][t],
                name=f"max_sales_p{p}_t{t}"
            )

    # Final inventory target constraints
    for p in products:
        try:
            target = final_inv_target[p]
        except (TypeError, KeyError):
            target = final_inv_target
        model.addConstr(
            inventory[p, num_periods - 1] == target,
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