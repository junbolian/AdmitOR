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

    # Build coverage sets: for each zone i, which candidates j can cover it
    coverage = {
        i: [j for j in candidates if distance_matrix[i][j] <= coverage_radius]
        for i in zones
    }

    # Check feasibility: every zone must have at least one candidate that can cover it
    for i in zones:
        if not coverage[i]:
            return {"objective": None, "status": f"zone {i+1} cannot be covered by any candidate"}

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary decision variables: open candidate station j or not
    x = model.addVars(candidates, vtype=GRB.BINARY, name="x")

    # Minimize total establishment cost
    model.setObjective(
        gp.quicksum(establishment_costs[j] * x[j] for j in candidates),
        GRB.MINIMIZE
    )

    # Coverage constraints: each zone must be covered by at least one open station
    for i in zones:
        model.addConstr(
            gp.quicksum(x[j] for j in coverage[i]) >= 1,
            name=f"cover_zone_{i+1}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}