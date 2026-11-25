import gurobipy as gp
from gurobipy import GRB

def solve(params):
    opening_costs = params["opening_costs"]
    coverage_radius = params["coverage_radius"]
    distance_matrix = params["distance_matrix"]

    num_zones = 20
    num_sites = 14

    zones = range(num_zones)
    sites = range(num_sites)

    # Build coverage sets: for each zone, which sites cover it
    covers = {}
    for i in zones:
        covers[i] = [j for j in sites if distance_matrix[i][j] <= coverage_radius]

    model = gp.Model("set_covering_5g")
    model.setParam("OutputFlag", 0)

    # Binary variable: deploy tower at site j
    x = model.addVars(sites, vtype=GRB.BINARY, name="x")

    # Minimize total deployment cost
    model.setObjective(
        gp.quicksum(opening_costs[j] * x[j] for j in sites),
        GRB.MINIMIZE
    )

    # Every zone must be covered by at least one deployed tower
    for i in zones:
        if len(covers[i]) == 0:
            return {"objective": None, "status": "infeasible: zone uncoverable"}
        model.addConstr(
            gp.quicksum(x[j] for j in covers[i]) >= 1,
            name=f"cover_zone_{i}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver status {model.Status}"}