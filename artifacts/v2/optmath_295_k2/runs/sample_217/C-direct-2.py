import gurobipy as gp
from gurobipy import GRB

def solve(params):
    team_costs = params["team_costs"]
    requirement_thresholds = params["requirement_thresholds"]

    # Coverage sets for each of the 20 requirements (0-indexed teams)
    coverage_sets = [
        [0, 3, 4],           # Req 1: Teams 1,4,5
        [1, 6, 7, 8, 9],     # Req 2: Teams 2,7,8,9,10
        [0, 1, 3, 4],        # Req 3: Teams 1,2,4,5
        [1, 2, 4, 5, 7, 8],  # Req 4: Teams 2,3,5,6,8,9
        [0, 10],             # Req 5: Teams 1,11
        [4, 5, 6, 7],        # Req 6: Teams 5,6,7,8
        [1, 5, 8],           # Req 7: Teams 2,6,9
        [0, 1, 2, 7, 8],     # Req 8: Teams 1,2,3,8,9
        [0, 3, 6],           # Req 9: Teams 1,4,7
        [1, 2, 6, 9],        # Req 10: Teams 2,3,7,10
        [2, 3, 4, 6, 7],     # Req 11: Teams 3,4,5,7,8
        [0, 3, 4, 7, 8, 9],  # Req 12: Teams 1,4,5,8,9,10
        [0, 2, 4, 6, 7, 8, 9],      # Req 13: Teams 1,3,5,7,8,9,10
        [0, 2, 3, 4, 5, 7, 9, 10],  # Req 14: Teams 1,3,4,5,6,8,10,11
        [2, 7, 8, 10],       # Req 15: Teams 3,8,9,11
        [1, 4, 5, 10],       # Req 16: Teams 2,5,6,11
        [2, 7, 10],          # Req 17: Teams 3,8,11
        [2, 3, 5, 7, 8, 9],  # Req 18: Teams 3,4,6,8,9,10
        [0, 3, 4, 8],        # Req 19: Teams 1,4,5,9
        [0, 4, 5, 9],        # Req 20: Teams 1,5,6,10
    ]

    n_teams = 11
    n_reqs = 20

    model = gp.Model("team_deployment")
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
        teams_in_set = coverage_sets[r]
        threshold = requirement_thresholds[r]
        model.addConstr(
            gp.quicksum(x[i] for i in teams_in_set) >= threshold,
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