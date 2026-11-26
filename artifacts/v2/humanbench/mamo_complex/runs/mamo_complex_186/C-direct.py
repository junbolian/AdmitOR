import gurobipy as gp
from gurobipy import GRB

def solve(params):
    opening_cost = params["opening_cost"]  # list of 9 values
    transport_cost = params["transport_cost"]  # 9x5 matrix
    demand = params["demand"]  # list of 5 values
    capacity = params["capacity"]  # list of 9 values

    num_centers = 9
    num_stores = 5
    centers = range(num_centers)
    stores = range(num_stores)

    model = gp.Model("GlobalSupply")
    model.setParam("OutputFlag", 0)

    # Decision variables
    # y[i] = 1 if distribution center i is opened
    y = model.addVars(centers, vtype=GRB.BINARY, name="y")
    # x[i,j] = units shipped from center i to store j
    x = model.addVars(centers, stores, vtype=GRB.CONTINUOUS, lb=0.0, name="x")

    # Objective: minimize opening costs + transportation costs
    model.setObjective(
        gp.quicksum(opening_cost[i] * y[i] for i in centers) +
        gp.quicksum(transport_cost[i][j] * x[i, j] for i in centers for j in stores),
        GRB.MINIMIZE
    )

    # Demand constraints: each store's demand must be fully met
    for j in stores:
        model.addConstr(
            gp.quicksum(x[i, j] for i in centers) >= demand[j],
            name=f"demand_{j}"
        )

    # Capacity constraints: shipments from center i cannot exceed its capacity (only if open)
    for i in centers:
        model.addConstr(
            gp.quicksum(x[i, j] for j in stores) <= capacity[i] * y[i],
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