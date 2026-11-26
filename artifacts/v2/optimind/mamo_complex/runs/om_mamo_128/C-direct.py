import gurobipy as gp
from gurobipy import GRB

def solve(params):
    opening_cost = params["opening_cost"]
    transport_cost = params["transport_cost"]
    demand = params["demand"]
    capacity = params["capacity"]

    num_centers = 6
    num_stores = 8
    centers = range(num_centers)
    stores = range(num_stores)

    model = gp.Model("SwiftLogistics")
    model.setParam("OutputFlag", 0)

    # Decision variables
    # y[i] = 1 if distribution center i is opened
    y = model.addVars(centers, vtype=GRB.BINARY, name="open")
    # x[i][j] = units shipped from center i to store j
    x = model.addVars(centers, stores, vtype=GRB.CONTINUOUS, lb=0.0, name="ship")

    # Objective: minimize opening costs + transportation costs
    model.setObjective(
        gp.quicksum(opening_cost[i] * y[i] for i in centers) +
        gp.quicksum(transport_cost[i][j] * x[i, j] for i in centers for j in stores),
        GRB.MINIMIZE
    )

    # Demand constraints: each store must receive exactly its demand
    for j in stores:
        model.addConstr(
            gp.quicksum(x[i, j] for i in centers) == demand[j],
            name=f"demand_{j}"
        )

    # Capacity constraints: a center can only ship up to its capacity if opened
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