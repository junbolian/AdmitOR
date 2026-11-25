import gurobipy as gp
from gurobipy import GRB

def solve(params):
    production_cost = params["production_cost"]
    fixed_order_cost = params["fixed_order_cost"]
    holding_cost = params["holding_cost"]
    backlog_cost = params["backlog_cost"]
    demand = params["demand"]
    production_capacity = params["production_capacity"]

    T = 6
    months = range(T)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables
    order = model.addVars(T, vtype=GRB.BINARY, name="order")
    produce = model.addVars(T, lb=0.0, name="produce")
    inventory = model.addVars(T, lb=0.0, name="inventory")
    backlog = model.addVars(T, lb=0.0, name="backlog")

    # Production capacity constraint: produce[t] <= capacity * order[t]
    for t in months:
        model.addConstr(produce[t] <= production_capacity * order[t], name=f"capacity_{t}")

    # Inventory balance constraints
    for t in months:
        prev_inv = 0.0 if t == 0 else inventory[t - 1]
        prev_bl = 0.0 if t == 0 else backlog[t - 1]
        model.addConstr(
            inventory[t] - backlog[t] == prev_inv - prev_bl + produce[t] - demand[t],
            name=f"balance_{t}"
        )

    # No inventory or backlog after Month 6
    model.addConstr(inventory[T - 1] == 0, name="no_final_inventory")
    model.addConstr(backlog[T - 1] == 0, name="no_final_backlog")

    # Objective
    obj = gp.quicksum(
        production_cost[t] * produce[t]
        + fixed_order_cost[t] * order[t]
        + holding_cost[t] * inventory[t]
        + backlog_cost[t] * backlog[t]
        for t in months
    )
    model.setObjective(obj, GRB.MINIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}