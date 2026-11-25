import gurobipy as gp
from gurobipy import GRB

def solve(params):
    establishment_costs = params["establishment_costs"]
    coverage_radius = params["coverage_radius"]
    distance_matrix = params["distance_matrix"]

    num_zones = len(distance_matrix)
    num_candidates = len(establishment_costs)

    # Precompute coverage sets: for each zone, which candidates cover it
    covers = {}
    for i in range(num_zones):
        covers[i] = [j for j in range(num_candidates)
                     if distance_matrix[i][j] <= coverage_radius]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary variable: open candidate station j or not
    x = model.addVars(num_candidates, vtype=GRB.BINARY, name="x")

    # Objective: minimize total establishment cost
    model.setObjective(
        gp.quicksum(establishment_costs[j] * x[j] for j in range(num_candidates)),
        GRB.MINIMIZE
    )

    # Coverage constraints: every zone must be covered by at least one open station
    for i in range(num_zones):
        if len(covers[i]) == 0:
            # Zone i cannot be covered by any candidate — infeasible by construction
            return {"objective": None, "status": "infeasible: zone uncoverable"}
        model.addConstr(
            gp.quicksum(x[j] for j in covers[i]) >= 1,
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