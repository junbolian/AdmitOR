import gurobipy as gp
from gurobipy import GRB

def solve(params):
    team_costs = params["team_costs"]
    requirement_thresholds = params["requirement_thresholds"]

    # Coverage sets (1-indexed teams, converted to 0-indexed)
    coverage_sets = [
        [1, 4, 5],
        [2, 7, 8, 9, 10],
        [1, 2, 4, 5],
        [2, 3, 5, 6, 8, 9],
        [1, 11],
        [5, 6, 7, 8],
        [2, 6, 9],
        [1, 2, 3, 8, 9],
        [1, 4, 7],
        [2, 3, 7, 10],
        [3, 4, 5, 7, 8],
        [1, 4, 5, 8, 9, 10],
        [1, 3, 5, 7, 8, 9, 10],
        [1, 3, 4, 5, 6, 8, 10, 11],
        [3, 8, 9, 11],
        [2, 5, 6, 11],
        [3, 8, 11],
        [3, 4, 6, 8, 9, 10],
        [1, 4, 5, 9],
        [1, 5, 6, 10],
    ]
    # Convert to 0-indexed
    coverage_sets_0 = [[t - 1 for t in s] for s in coverage_sets]

    n_teams = 11
    n_reqs = 20

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary decision variables: deploy team i or not
    x = model.addVars(n_teams, vtype=GRB.BINARY, name="x")

    # Objective: minimize total deployment cost
    model.setObjective(
        gp.quicksum(team_costs[i] * x[i] for i in range(n_teams)),
        GRB.MINIMIZE
    )

    # Coverage constraints
    for r in range(n_reqs):
        model.addConstr(
            gp.quicksum(x[i] for i in coverage_sets_0[r]) >= requirement_thresholds[r],
            name=f"req_{r}"
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