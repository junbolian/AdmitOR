import gurobipy as gp
from gurobipy import GRB

def solve(params):
    demand = params["demand"]                      # list of 6 monthly demands
    regular_capacity = params["regular_capacity"]  # scalar or list
    regular_cost = params["regular_cost"]
    overtime_capacity = params["overtime_capacity"]
    overtime_cost = params["overtime_cost"]
    inventory_cost = params["inventory_cost"]
    initial_inventory = params["initial_inventory"]

    months = range(6)

    # Allow regular_capacity and overtime_capacity to be scalar or list
    if isinstance(regular_capacity, (int, float)):
        reg_cap = [regular_capacity] * 6
    else:
        reg_cap = list(regular_capacity)

    if isinstance(overtime_capacity, (int, float)):
        ot_cap = [overtime_capacity] * 6
    else:
        ot_cap = list(overtime_capacity)

    model = gp.Model("BTD_Wrench")
    model.setParam("OutputFlag", 0)

    # Decision variables
    reg = model.addVars(6, lb=0.0, name="reg")   # regular production
    ovt = model.addVars(6, lb=0.0, name="ovt")   # overtime production
    inv = model.addVars(6, lb=0.0, name="inv")   # end-of-month inventory

    # Capacity constraints
    for t in months:
        model.addConstr(reg[t] <= reg_cap[t], name=f"reg_cap_{t}")
        model.addConstr(ovt[t] <= ot_cap[t], name=f"ot_cap_{t}")

    # Inventory balance constraints
    for t in months:
        if t == 0:
            prev_inv = initial_inventory
        else:
            prev_inv = inv[t - 1]
        model.addConstr(
            prev_inv + reg[t] + ovt[t] - inv[t] == demand[t],
            name=f"balance_{t}"
        )

    # Objective: minimize total cost
    total_cost = (
        gp.quicksum(regular_cost * reg[t] + overtime_cost * ovt[t] + inventory_cost * inv[t]
                    for t in months)
    )
    model.setObjective(total_cost, GRB.MINIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": round(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}