import gurobipy as gp
from gurobipy import GRB

def solve(params):
    establishment_costs = params["establishment_costs"]
    coverage_radius = params["coverage_radius"]
    distance_matrix = params["distance_matrix"]

    num_zones = 29
    num_candidates = 10

    zones = range(num_zones)
    candidates = range(num_candidates)

    # Precompute coverage sets: for each zone i, which candidates j can cover it
    can_cover = {
        i: [j for j in candidates if distance_matrix[i][j] <= coverage_radius]
        for i in zones
    }

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary variable: open candidate station j or not
    x = model.addVars(candidates, vtype=GRB.BINARY, name="x")

    # Objective: minimize total establishment cost
    model.setObjective(
        gp.quicksum(establishment_costs[j] * x[j] for j in candidates),
        GRB.MINIMIZE
    )

    # Coverage constraints: every zone must be covered by at least one open station
    for i in zones:
        covering = can_cover[i]
        if not covering:
            # No candidate can cover this zone — infeasible by construction
            return {"objective": None, "status": "infeasible: zone uncoverable"}
        model.addConstr(
            gp.quicksum(x[j] for j in covering) >= 1,
            name=f"cover_zone_{i}"
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