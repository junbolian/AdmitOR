import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit_per_unit = params["profit_per_unit"]
    holding_cost = params["holding_cost"]
    machine_hours_grinders = params["machine_hours_grinders"]
    machine_hours_drills = params["machine_hours_drills"]
    machine_hours_borers = params["machine_hours_borers"]
    time_req_grinders = params["time_req_grinders"]
    time_req_drills = params["time_req_drills"]
    time_req_borers = params["time_req_borers"]
    inventory_capacity = params["inventory_capacity"]
    sales_limit_p0 = params["sales_limit_p0"]
    sales_limit_p1 = params["sales_limit_p1"]
    sales_limit_p2 = params["sales_limit_p2"]
    target_inventory = params["target_inventory"]

    n_products = 3
    n_periods = 5
    products = range(n_products)
    periods = range(n_periods)

    sales_limits = [sales_limit_p0, sales_limit_p1, sales_limit_p2]

    # target_inventory may be a scalar or a sequence; normalise to a list
    if hasattr(target_inventory, "__len__"):
        target_inv_list = list(target_inventory)
    else:
        target_inv_list = [target_inventory] * n_products

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    produce = model.addVars(n_products, n_periods, lb=0.0, name="produce")
    inventory = model.addVars(n_products, n_periods, lb=0.0, name="inventory")
    sales = model.addVars(n_products, n_periods, lb=0.0, name="sales")

    # Objective: maximise revenue minus holding costs
    model.setObjective(
        gp.quicksum(profit_per_unit[p] * sales[p, t] for p in products for t in periods)
        - gp.quicksum(holding_cost * inventory[p, t] for p in products for t in periods),
        GRB.MAXIMIZE
    )

    # Inventory balance constraints
    for p in products:
        for t in periods:
            if t == 0:
                model.addConstr(
                    produce[p, t] == sales[p, t] + inventory[p, t],
                    name=f"balance_p{p}_t{t}"
                )
            else:
                model.addConstr(
                    inventory[p, t - 1] + produce[p, t] == sales[p, t] + inventory[p, t],
                    name=f"balance_p{p}_t{t}"
                )

    # Machine capacity constraints
    for t in periods:
        model.addConstr(
            gp.quicksum(time_req_grinders[p] * produce[p, t] for p in products)
            <= machine_hours_grinders[t],
            name=f"grinder_t{t}"
        )
        model.addConstr(
            gp.quicksum(time_req_drills[p] * produce[p, t] for p in products)
            <= machine_hours_drills[t],
            name=f"drill_t{t}"
        )
        model.addConstr(
            gp.quicksum(time_req_borers[p] * produce[p, t] for p in products)
            <= machine_hours_borers[t],
            name=f"borer_t{t}"
        )

    # Inventory capacity constraints
    for p in products:
        for t in periods:
            model.addConstr(
                inventory[p, t] <= inventory_capacity,
                name=f"inv_cap_p{p}_t{t}"
            )

    # Sales limit constraints
    for p in products:
        for t in periods:
            model.addConstr(
                sales[p, t] <= sales_limits[p][t],
                name=f"sales_lim_p{p}_t{t}"
            )

    # Target inventory at end of horizon (period 4)
    for p in products:
        model.addConstr(
            inventory[p, n_periods - 1] == target_inv_list[p],
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
        return {"objective": None, "status": f"status_{model.Status}"}