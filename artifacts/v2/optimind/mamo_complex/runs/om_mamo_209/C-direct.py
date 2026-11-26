import gurobipy as gp
from gurobipy import GRB

def solve(params):
    demand = params["demand"]
    initial_inventory = params["initial_inventory"]
    regular_capacity = params["regular_capacity"]
    regular_cost = params["regular_cost"]
    overtime_cost = params["overtime_cost"]
    holding_cost = params["holding_cost"]

    quarters = range(4)

    model = gp.Model("sailco")
    model.setParam("OutputFlag", 0)

    # Decision variables
    regular = model.addVars(quarters, lb=0.0, name="regular")
    overtime = model.addVars(quarters, lb=0.0, name="overtime")
    inventory = model.addVars(quarters, lb=0.0, name="inventory")

    # Regular time capacity constraints
    for t in quarters:
        model.addConstr(regular[t] <= regular_capacity, name=f"reg_cap_{t}")

    # Inventory balance constraints
    for t in quarters:
        if t == 0:
            prev_inv = initial_inventory
        else:
            prev_inv = inventory[t - 1]
        model.addConstr(
            prev_inv + regular[t] + overtime[t] - demand[t] == inventory[t],
            name=f"balance_{t}"
        )

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(regular_cost * regular[t] + overtime_cost * overtime[t] + holding_cost * inventory[t]
                    for t in quarters),
        GRB.MINIMIZE
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