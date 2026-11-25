import gurobipy as gp
from gurobipy import GRB


def solve(params):
    fixed_setup_cost = params["fixed_setup_cost"]
    latency_matrix = params["latency_matrix"]
    num_end_users = params["num_end_users"]
    num_locations = params["num_locations"]
    # user_coordinates and location_coordinates are provided but not needed
    # beyond what's already captured in latency_matrix

    users = range(num_end_users)
    locations = range(num_locations)

    model = gp.Model("cloud_data_center")
    model.setParam("OutputFlag", 0)

    # y[j] = 1 if location j is opened
    y = model.addVars(locations, vtype=GRB.BINARY, name="y")

    # x[i, j] = 1 if user i is assigned to location j
    x = model.addVars(users, locations, vtype=GRB.BINARY, name="x")

    # Objective: fixed setup costs + total latency
    model.setObjective(
        gp.quicksum(fixed_setup_cost[j] * y[j] for j in locations)
        + gp.quicksum(latency_matrix[i][j] * x[i, j] for i in users for j in locations),
        GRB.MINIMIZE,
    )

    # Each user assigned to exactly one location
    for i in users:
        model.addConstr(gp.quicksum(x[i, j] for j in locations) == 1, name=f"assign_{i}")

    # Assignment only to open locations
    for i in users:
        for j in locations:
            model.addConstr(x[i, j] <= y[j], name=f"link_{i}_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}