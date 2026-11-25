import gurobipy as gp
from gurobipy import GRB

def solve(params):
    num_towers = params["num_towers_to_select"]
    radius = params["service_radius_km"]
    demands = params["community_demands"]
    dist_matrix = params["distance_matrix"]

    num_communities = len(demands)
    num_sites = len(dist_matrix[0])

    communities = range(num_communities)
    sites = range(num_sites)

    # coverage[i][j] = 1 if site j covers community i
    coverage = [
        [1 if dist_matrix[i][j] <= radius else 0 for j in sites]
        for i in communities
    ]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[j] = 1 if tower site j is selected
    x = model.addVars(sites, vtype=GRB.BINARY, name="x")
    # y[i] = 1 if community i is covered
    y = model.addVars(communities, vtype=GRB.BINARY, name="y")

    # Exactly num_towers sites selected
    model.addConstr(gp.quicksum(x[j] for j in sites) == num_towers, name="cardinality")

    # Community i can only be covered if at least one covering tower is selected
    for i in communities:
        covering_sites = [j for j in sites if coverage[i][j] == 1]
        if covering_sites:
            model.addConstr(
                y[i] <= gp.quicksum(x[j] for j in covering_sites),
                name=f"cover_{i}"
            )
        else:
            model.addConstr(y[i] == 0, name=f"cover_{i}_none")

    # Maximize total demand of covered communities
    model.setObjective(
        gp.quicksum(demands[i] * y[i] for i in communities),
        GRB.MAXIMIZE
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