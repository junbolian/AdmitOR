import gurobipy as gp
from gurobipy import GRB


def solve(params):
    installation_costs = params["installation_costs"]
    walking_distances = params["walking_distances"]
    num_stops = params["num_stops"]
    num_sites = params["num_sites"]

    stops = range(num_stops)
    sites = range(num_sites)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # y[j] = 1 if site j is installed
    y = model.addVars(sites, vtype=GRB.BINARY, name="y")

    # x[i, j] = 1 if stop i is assigned to site j
    x = model.addVars(stops, sites, vtype=GRB.BINARY, name="x")

    # Objective: minimize installation costs + total walking distance
    model.setObjective(
        gp.quicksum(installation_costs[j] * y[j] for j in sites)
        + gp.quicksum(walking_distances[i][j] * x[i, j] for i in stops for j in sites),
        GRB.MINIMIZE
    )

    # Each stop assigned to exactly one site
    for i in stops:
        model.addConstr(gp.quicksum(x[i, j] for j in sites) == 1, name=f"assign_{i}")

    # Can only assign to an open site
    for i in stops:
        for j in sites:
            model.addConstr(x[i, j] <= y[j], name=f"open_{i}_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}