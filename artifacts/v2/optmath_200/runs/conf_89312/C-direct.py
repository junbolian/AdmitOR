import gurobipy as gp
from gurobipy import GRB

def solve(params):
    demand = params["demand"]
    production_cost = params["production_cost"]
    inventory_cost = params["inventory_cost"]
    backlog_cost = params["backlog_cost"]
    setup_cost = params["setup_cost"]
    production_capacity = params["production_capacity"]

    T = 5  # number of months
    months = range(T)  # 0-indexed: 0..4

    model = gp.Model("production_planning")
    model.setParam("OutputFlag", 0)

    # Decision variables
    produce = model.addVars(T, lb=0.0, name="OrderedAmount")
    inventory = model.addVars(T, lb=0.0, name="EndingInventory")
    backlog = model.addVars(T, lb=0.0, name="BackloggedAmount")
    setup = model.addVars(T, vtype=GRB.BINARY, name="OrderIsPlaced")

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(
            setup_cost[t] * setup[t]
            + production_cost[t] * produce[t]
            + inventory_cost[t] * inventory[t]
            + backlog_cost[t] * backlog[t]
            for t in months
        ),
        GRB.MINIMIZE
    )

    # Demand fulfillment constraints (inventory balance)
    # For month 0 (first month): no prior inventory or backlog
    # inventory[t] - backlog[t] = inventory[t-1] - backlog[t-1] + produce[t] - demand[t]
    # With inventory[-1] = 0, backlog[-1] = 0

    for t in months:
        if t == 0:
            prev_inv = 0.0
            prev_backlog = 0.0
        else:
            prev_inv = inventory[t - 1]
            prev_backlog = backlog[t - 1]
        model.addConstr(
            prev_inv - prev_backlog + produce[t] - demand[t] == inventory[t] - backlog[t],
            name=f"balance_{t}"
        )

    # No inventory or backlog at end of month 5 (index 4)
    model.addConstr(inventory[T - 1] == 0, name="end_inventory")
    model.addConstr(backlog[T - 1] == 0, name="end_backlog")

    # Production capacity: produce[t] <= capacity * setup[t]
    for t in months:
        model.addConstr(
            produce[t] <= production_capacity * setup[t],
            name=f"capacity_{t}"
        )

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{status}"}