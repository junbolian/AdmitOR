import gurobipy as gp
from gurobipy import GRB

def solve(params):
    demands = params["demands"]
    coverage_threshold_km = params["coverage_threshold_km"]
    num_sites_to_deploy = params["num_sites_to_deploy"]
    distance_matrix = params["distance_matrix"]

    num_communities = len(demands)
    num_sites = len(distance_matrix[0])

    # covered[i][j] = 1 if community i is within threshold of site j
    covered = [
        [1 if distance_matrix[i][j] <= coverage_threshold_km else 0
         for j in range(num_sites)]
        for i in range(num_communities)
    ]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # y[j] = 1 if site j is deployed
    y = model.addVars(num_sites, vtype=GRB.BINARY, name="y")
    # z[i] = 1 if community i is covered by at least one deployed site
    z = model.addVars(num_communities, vtype=GRB.BINARY, name="z")

    # Exactly num_sites_to_deploy sites deployed
    model.addConstr(gp.quicksum(y[j] for j in range(num_sites)) == num_sites_to_deploy)

    # z[i] can be 1 only if at least one covering site is deployed
    for i in range(num_communities):
        eligible_sites = [j for j in range(num_sites) if covered[i][j] == 1]
        if eligible_sites:
            model.addConstr(z[i] <= gp.quicksum(y[j] for j in eligible_sites))
        else:
            model.addConstr(z[i] == 0)

    # Maximize total demand of covered communities
    model.setObjective(
        gp.quicksum(demands[i] * z[i] for i in range(num_communities)),
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
        return {"objective": None, "status": f"solver_status_{model.Status}"}