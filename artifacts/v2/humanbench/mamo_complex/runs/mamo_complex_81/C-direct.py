import gurobipy as gp
from gurobipy import GRB

def solve(params):
    opening_cost = params["opening_cost"]      # list of length 6
    transport_cost = params["transport_cost"]  # 6x4 list of lists
    demand = params["demand"]                  # list of length 4
    capacity = params["capacity"]              # list of length 6

    num_centers = 6
    num_stores = 4

    centers = range(num_centers)
    stores = range(num_stores)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary: open center i
    open_var = model.addVars(centers, vtype=GRB.BINARY, name="open")

    # Continuous: units shipped from center i to store j
    ship = model.addVars(centers, stores, lb=0.0, vtype=GRB.CONTINUOUS, name="ship")

    # Objective: opening costs + transportation costs
    model.setObjective(
        gp.quicksum(opening_cost[i] * open_var[i] for i in centers) +
        gp.quicksum(transport_cost[i][j] * ship[i, j] for i in centers for j in stores),
        GRB.MINIMIZE
    )

    # Demand constraints: each store's demand must be met
    for j in stores:
        model.addConstr(
            gp.quicksum(ship[i, j] for i in centers) >= demand[j],
            name=f"demand_{j}"
        )

    # Capacity constraints: total shipped from center i <= capacity if open
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