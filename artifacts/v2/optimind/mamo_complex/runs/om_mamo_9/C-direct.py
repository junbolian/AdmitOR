import gurobipy as gp
from gurobipy import GRB

def solve(params):
    # Try both possible key names for the transportation cost matrix
    if "transport_cost" in params:
        transport_cost = params["transport_cost"]
    else:
        transport_cost = params["transportation_cost"]

    opening_cost = params["opening_cost"]      # list of length 6
    demand = params["demand"]                  # list of length 8
    capacity = params["capacity"]              # list of length 6

    num_centers = 6
    num_stores = 8

    centers = range(num_centers)
    stores = range(num_stores)

    model = gp.Model("facility_location")
    model.setParam("OutputFlag", 0)

    # Binary: open distribution center i
    open_dc = model.addVars(centers, vtype=GRB.BINARY, name="open")

    # Continuous: units shipped from center i to store j
    ship = model.addVars(centers, stores, vtype=GRB.CONTINUOUS, lb=0.0, name="ship")

    # Objective: minimize opening costs + transportation costs
    model.setObjective(
        gp.quicksum(opening_cost[i] * open_dc[i] for i in centers) +
        gp.quicksum(transport_cost[i][j] * ship[i, j] for i in centers for j in stores),
        GRB.MINIMIZE
    )

    # Demand satisfaction: each store's demand must be fully met
    for j in stores:
        model.addConstr(
            gp.quicksum(ship[i, j] for i in centers) >= demand[j],
            name=f"demand_{j}"
        )

    # Capacity: shipments from center i cannot exceed its capacity (and only if open)
    for i in centers:
        model.addConstr(
            gp.quicksum(ship[i, j] for j in stores) <= capacity[i] * open_dc[i],
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
        return {"objective": None, "status": f"solver_status_{model.Status}"}