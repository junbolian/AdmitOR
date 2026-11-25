import gurobipy as gp
from gurobipy import GRB

def solve(params):
    team_costs = params["team_costs"]

    # Coverage sets: for each location (0-indexed), which teams (0-indexed) can cover it
    coverage = [
        [0, 1, 3, 4, 5, 6, 8],      # Location 1
        [0, 2, 3, 4, 5, 8, 9],      # Location 2
        [0, 1, 2, 3, 7, 9],         # Location 3
        [1, 4, 7, 9],               # Location 4
        [0, 6],                     # Location 5
        [0, 1, 2, 4, 7, 8, 9],      # Location 6
        [0, 1, 3, 4, 8],            # Location 7
        [2, 7, 8],                  # Location 8
        [2, 3, 4, 6],               # Location 9
        [0, 1, 4, 5],               # Location 10
        [1, 2, 6, 8],               # Location 11
        [4, 6, 7, 8, 9],            # Location 12
        [1, 2, 7, 9],               # Location 13
        [0, 1, 2, 4, 5, 8, 9],      # Location 14
        [1, 5, 7, 8],               # Location 15
        [1, 2, 4, 6, 9],            # Location 16
        [0, 1, 2, 4, 7, 8, 9],      # Location 17
    ]

    num_teams = 10
    num_locations = 17

    model = gp.Model("emergency_coverage")
    model.setParam("OutputFlag", 0)

    # Binary decision variables: deploy team j or not
    x = model.addVars(num_teams, vtype=GRB.BINARY, name="x")

    # Objective: minimize total deployment cost
    model.setObjective(
        gp.quicksum(team_costs[j] * x[j] for j in range(num_teams)),
        GRB.MINIMIZE
    )

    # Coverage constraints: each location must be covered by at least one capable team
    for loc_idx in range(num_locations):
        capable_teams = coverage[loc_idx]
        model.addConstr(
            gp.quicksum(x[j] for j in capable_teams) >= 1,
            name=f"cover_loc_{loc_idx}"
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