import gurobipy as gp
from gurobipy import GRB

def solve(params):
    opening_cost = params["opening_cost"]   # list of 6 floats
    transport_cost = params["transport_cost"]  # 6x5 list of lists
    demand = params["demand"]               # list of 5 floats
    capacity = params["capacity"]           # list of 6 floats

    num_centers = 6
    num_stores = 5
    centers = range(num_centers)
    stores = range(num_stores)

    model = gp.Model("supply_chain")
    model.Params.OutputFlag = 0

    # Binary: open center i
    y = model.addVars(centers, vtype=GRB.BINARY, name="open")

    # Continuous: units shipped from center i to store j
    x = model.addVars(centers, stores, vtype=GRB.CONTINUOUS, lb=0.0, name="ship")

    # Objective: minimize total opening + transportation cost
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

    # Capacity constraints: a center can only ship up to its capacity if open
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