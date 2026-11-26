import gurobipy as gp
from gurobipy import GRB

def solve(params):
    opening_cost = params["opening_cost"]      # list of 5 floats
    transport_cost = params["transport_cost"]  # 5x5 list of lists
    demand = params["demand"]                  # list of 5 floats
    capacity = params["capacity"]              # list of 5 floats

    n_centers = 5
    n_stores = 5
    centers = range(n_centers)
    stores = range(n_stores)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary: open center i
    open_var = model.addVars(centers, vtype=GRB.BINARY, name="open")

    # Continuous: units shipped from center i to store j
    ship = model.addVars(centers, stores, vtype=GRB.CONTINUOUS, lb=0.0, name="ship")

    # Objective: opening costs + transportation costs
    model.setObjective(
        gp.quicksum(opening_cost[i] * open_var[i] for i in centers) +
        gp.quicksum(transport_cost[i][j] * ship[i, j] for i in centers for j in stores),
        GRB.MINIMIZE
    )

    # Demand satisfaction: each store j must receive at least its demand
    for j in stores:
        model.addConstr(
            gp.quicksum(ship[i, j] for i in centers) >= demand[j],
            name=f"demand_{j}"
        )

    # Capacity: total shipped from center i cannot exceed its capacity (and only if open)
    for i in centers:
        model.addConstr(
            gp.quicksum(ship[i, j] for j in stores) <= capacity[i] * open_var[i],
            name=f"capacity_{i}"
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