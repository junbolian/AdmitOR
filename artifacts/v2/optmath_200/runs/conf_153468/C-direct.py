import gurobipy as gp
from gurobipy import GRB

def solve(params):
    revenue = params["revenue"]          # list of length 3
    holding_cost = params["holding_cost"]  # scalar
    grinder_capacity = params["grinder_capacity"]  # scalar (hours per period)
    drill_capacity = params["drill_capacity"]       # scalar
    borer_capacity = params["borer_capacity"]       # scalar
    grinder_time = params["grinder_time"]  # list of length 3
    drill_time = params["drill_time"]      # list of length 3
    borer_time = params["borer_time"]      # list of length 3
    max_inventory = params["max_inventory"]  # scalar or list; treat as per-product-per-period cap
    sales_limits = params["sales_limits"]    # 4x3 array: row=period, col=product
    target_inventory = params["target_inventory"]  # list of length 3

    num_products = 3
    num_periods = 4
    products = range(num_products)
    periods = range(num_periods)

    model = gp.Model("factory_planning")
    model.setParam("OutputFlag", 0)

    # Decision variables
    produce = model.addVars(num_periods, num_products, lb=0.0, name="produce")
    inventory = model.addVars(num_periods, num_products, lb=0.0, name="inventory")
    sell = model.addVars(num_periods, num_products, lb=0.0, name="sell")

    # Objective: maximize revenue from sales minus holding costs
    model.setObjective(
        gp.quicksum(revenue[p] * sell[t, p] for t in periods for p in products)
        - gp.quicksum(holding_cost * inventory[t, p] for t in periods for p in products),
        GRB.MAXIMIZE
    )

    # Initial balance (Period 0): production = sales + inventory
    for p in products:
        model.addConstr(
            produce[0, p] == sell[0, p] + inventory[0, p],
            name=f"init_balance_p{p}"
        )

    # Inventory flow for periods 1..3
    for t in range(1, num_periods):
        for p in products:
            model.addConstr(
                inventory[t - 1, p] + produce[t, p] == sell[t, p] + inventory[t, p],
                name=f"flow_t{t}_p{p}"
            )

    # Machine capacity constraints
    for t in periods:
        model.addConstr(
            gp.quicksum(grinder_time[p] * produce[t, p] for p in products) <= grinder_capacity,
            name=f"grinder_t{t}"
        )
        model.addConstr(
            gp.quicksum(drill_time[p] * produce[t, p] for p in products) <= drill_capacity,
            name=f"drill_t{t}"
        )
        model.addConstr(
            gp.quicksum(borer_time[p] * produce[t, p] for p in products) <= borer_capacity,
            name=f"borer_t{t}"
        )

    # Inventory limits
    for t in periods:
        for p in products:
            # max_inventory may be a scalar or a nested structure; handle both
            if hasattr(max_inventory, '__len__'):
                try:
                    cap = max_inventory[t][p]
                except (TypeError, IndexError, KeyError):
                    try:
                        cap = max_inventory[p]
                    except (TypeError, IndexError, KeyError):
                        cap = max_inventory
            else:
                cap = max_inventory
            model.addConstr(inventory[t, p] <= cap, name=f"inv_cap_t{t}_p{p}")

    # Sales limits
    for t in periods:
        for p in products:
            model.addConstr(sell[t, p] <= sales_limits[t][p], name=f"sales_lim_t{t}_p{p}")

    # Target inventory at end of horizon (Period 3)
    for p in products:
        model.addConstr(inventory[num_periods - 1, p] == target_inventory[p], name=f"target_inv_p{p}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}