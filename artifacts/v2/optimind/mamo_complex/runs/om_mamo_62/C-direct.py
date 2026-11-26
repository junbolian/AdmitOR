import gurobipy as gp
from gurobipy import GRB

def solve(params):
    opening_costs = params["opening_costs"]   # list of length num_centers
    transport_costs = params["transport_costs"]  # 2D list [num_centers][num_stores]
    demands = params["demands"]              # list of length num_stores
    capacities = params["capacities"]        # list of length num_centers
    num_centers = params["num_centers"]      # int
    num_stores = params["num_stores"]        # int

    centers = range(num_centers)
    stores = range(num_stores)

    model = gp.Model("GlobalSupply")
    model.setParam("OutputFlag", 0)

    # Binary variable: open center i
    open_center = model.addVars(centers, vtype=GRB.BINARY, name="open")

    # Continuous variable: units shipped from center i to store j
    ship = model.addVars(centers, stores, vtype=GRB.CONTINUOUS, lb=0.0, name="ship")

    # Objective: minimize opening costs + transportation costs
    model.setObjective(
        gp.quicksum(opening_costs[i] * open_center[i] for i in centers)
        + gp.quicksum(transport_costs[i][j] * ship[i, j] for i in centers for j in stores),
        GRB.MINIMIZE
    )

    # Demand satisfaction: each store's demand must be fully met
    for j in stores:
        model.addConstr(
            gp.quicksum(ship[i, j] for i in centers) >= demands[j],
            name=f"demand_{j}"
        )

    # Capacity: a center can only ship up to its capacity, and only if open
    for i in centers:
        model.addConstr(
            gp.quicksum(ship[i, j] for j in stores) <= capacities[i] * open_center[i],
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