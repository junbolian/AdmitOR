import gurobipy as gp
from gurobipy import GRB


def solve(params):
    opening_cost = params["opening_cost"]
    coverage_radius = params["coverage_radius"]
    distance_matrix = params["distance_matrix"]

    num_zones = len(distance_matrix)
    num_sites = len(opening_cost)

    zones = range(num_zones)
    sites = range(num_sites)

    # Build coverage sets: for each zone, which sites cover it
    coverage = {
        i: [j for j in sites if distance_matrix[i][j] <= coverage_radius]
        for i in zones
    }

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary variable: open site j or not
    x = model.addVars(num_sites, vtype=GRB.BINARY, name="x")

    # Minimize total opening cost
    model.setObjective(
        gp.quicksum(opening_cost[j] * x[j] for j in sites),
        GRB.MINIMIZE
    )

    # Every zone must be covered by at least one open site
    for i in zones:
        covering = coverage[i]
        if not covering:
            return {"objective": None, "status": "infeasible: zone uncoverable"}
        model.addConstr(
            gp.quicksum(x[j] for j in covering) >= 1,
            name=f"cover_{i}"
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