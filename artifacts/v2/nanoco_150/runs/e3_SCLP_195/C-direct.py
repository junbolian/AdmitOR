import gurobipy as gp
from gurobipy import GRB


def solve(params):
    site_costs = params["site_costs"]
    coverage_radius = params["coverage_radius"]
    distances = params["zone_site_distances"]
    num_zones = int(params["num_zones"])
    num_sites = int(params["num_sites"])

    model = gp.Model("locker_site_covering")
    model.setParam("OutputFlag", 0)

    x = model.addVars(num_sites, vtype=GRB.BINARY, name="install")

    model.setObjective(
        gp.quicksum(site_costs[j] * x[j] for j in range(num_sites)),
        GRB.MINIMIZE,
    )

    for i in range(num_zones):
        covering_vars = [
            x[j]
            for j in range(num_sites)
            if distances[i][j] <= coverage_radius
        ]
        model.addConstr(gp.quicksum(covering_vars) >= 1, name=f"cover_zone_{i}")

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.status in (GRB.INFEASIBLE, GRB.INF_OR_UNBD):
        return {"objective": None, "status": "infeasible"}
    return {"objective": None, "status": "not_optimal"}