import gurobipy as gp
from gurobipy import GRB

def solve(params):
    regular_cost = params["regular_cost"]
    overtime_cost = params["overtime_cost"]
    holding_cost = params["holding_cost"]
    regular_capacity = params["regular_capacity"]
    initial_inventory = params["initial_inventory"]
    demand = params["demand"]  # list of 4 values

    num_quarters = 4

    model = gp.Model("sailco")
    model.setParam("OutputFlag", 0)

    # Decision variables
    # r[t]: regular-time production in quarter t
    # o[t]: overtime production in quarter t
    # inv[t]: inventory at end of quarter t
    r = model.addVars(num_quarters, lb=0.0, name="r")
    o = model.addVars(num_quarters, lb=0.0, name="o")
    inv = model.addVars(num_quarters, lb=0.0, name="inv")

    # Regular-time capacity constraints
    for t in range(num_quarters):
        model.addConstr(r[t] <= regular_capacity, name=f"reg_cap_{t}")

    # Inventory balance constraints
    for t in range(num_quarters):
        if t == 0:
            prev_inv = initial_inventory
        else:
            prev_inv = inv[t - 1]
        model.addConstr(
            prev_inv + r[t] + o[t] - demand[t] == inv[t],
            name=f"balance_{t}"
        )

    # Objective: minimize total production + holding costs
    model.setObjective(
        gp.quicksum(regular_cost * r[t] + overtime_cost * o[t] for t in range(num_quarters))
        + gp.quicksum(holding_cost * inv[t] for t in range(num_quarters)),
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