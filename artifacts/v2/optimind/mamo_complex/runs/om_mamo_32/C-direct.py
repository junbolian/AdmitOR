import gurobipy as gp
from gurobipy import GRB

def solve(params):
    opening_cost = params["opening_cost"]   # list of 5 values, index 0..4
    transport_cost = params["transport_cost"]  # 5x6 matrix
    demand = params["demand"]               # list of 6 values
    capacity = params["capacity"]           # list of 5 values

    num_dc = 5
    num_stores = 6
    dcs = range(num_dc)
    stores = range(num_stores)

    model = gp.Model("GlobalSupply")
    model.setParam("OutputFlag", 0)

    # Decision variables
    # y[i] = 1 if DC i is opened
    y = model.addVars(dcs, vtype=GRB.BINARY, name="y")
    # x[i,j] = units shipped from DC i to store j
    x = model.addVars(dcs, stores, lb=0.0, vtype=GRB.CONTINUOUS, name="x")

    # Objective: minimize total opening + transport costs
    model.setObjective(
        gp.quicksum(opening_cost[i] * y[i] for i in dcs) +
        gp.quicksum(transport_cost[i][j] * x[i, j] for i in dcs for j in stores),
        GRB.MINIMIZE
    )

    # Demand constraints: each store's demand must be met
    for j in stores:
        model.addConstr(
            gp.quicksum(x[i, j] for i in dcs) >= demand[j],
            name=f"demand_{j}"
        )

    # Capacity constraints: DC i can only ship up to its capacity if opened
    for i in dcs:
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