import gurobipy as gp
from gurobipy import GRB

def solve(params):
    establishment_cost = params["establishment_cost"]
    coverage_radius = params["coverage_radius"]
    distance_matrix = params["distance_matrix"]

    num_communities = 28
    num_sites = 10

    communities = range(num_communities)
    sites = range(num_sites)

    # Build coverage sets: for each community i, which sites j can cover it
    can_cover = {
        i: [j for j in sites if distance_matrix[i][j] <= coverage_radius]
        for i in communities
    }

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary variable: open site j or not
    open_site = model.addVars(sites, vtype=GRB.BINARY, name="open_site")

    # Minimize total establishment cost
    model.setObjective(
        gp.quicksum(establishment_cost[j] * open_site[j] for j in sites),
        GRB.MINIMIZE
    )

    # Every community must be covered by at least one open site
    for i in communities:
        covering = can_cover[i]
        if len(covering) == 0:
            return {"objective": None, "status": "infeasible: community cannot be covered"}
        model.addConstr(
            gp.quicksum(open_site[j] for j in covering) >= 1,
            name=f"cover_{i}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver status {model.Status}"}