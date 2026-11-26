import gurobipy as gp
from gurobipy import GRB

def solve(params):
    opening_cost = params["opening_cost"]    # list of 6
    transport_cost = params["transport_cost"]  # 6x7 matrix
    demand = params["demand"]                # list of 7
    capacity = params["capacity"]            # list of 6

    num_centers = 6
    num_stores = 7
    centers = range(num_centers)
    stores = range(num_stores)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Decision variables
    open_var = model.addVars(centers, vtype=GRB.BINARY, name="open")
    ship_var = model.addVars(centers, stores, vtype=GRB.CONTINUOUS, lb=0.0, name="ship")

    # Objective: minimize opening costs + transportation costs
    model.setObjective(
        gp.quicksum(opening_cost[i] * open_var[i] for i in centers) +
        gp.quicksum(transport_cost[i][j] * ship_var[i, j] for i in centers for j in stores),
        GRB.MINIMIZE
    )

    # Demand constraints: each store's demand must be met
    for j in stores:
        model.addConstr(
            gp.quicksum(ship_var[i, j] for i in centers) >= demand[j],
            name=f"demand_{j}"
        )

    # Capacity constraints: shipments from a center cannot exceed its capacity if open
    for i in centers:
        model.addConstr(
            gp.quicksum(ship_var[i, j] for j in stores) <= capacity[i] * open_var[i],
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