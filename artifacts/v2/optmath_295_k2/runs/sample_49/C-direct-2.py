import gurobipy as gp
from gurobipy import GRB

def solve(params):
    team_costs = params["team_costs"]
    location_requirements = params["location_requirements"]

    num_teams = 14
    num_locations = 21

    # Coverage sets: which teams can cover each location (0-indexed)
    coverage = {
        0:  [1, 4, 5, 6, 7, 8, 10, 13],   # Location 1
        1:  [1, 4, 6, 12],                  # Location 2
        2:  [0, 1, 3, 4, 5, 8, 9, 11, 12], # Location 3
        3:  [2, 5, 12, 13],                 # Location 4
        4:  [1, 5, 9],                      # Location 5
        5:  [3, 5, 7, 13],                  # Location 6
        6:  [0, 3, 4, 7, 9, 10, 11, 12, 13], # Location 7
        7:  [0, 4, 10, 13],                 # Location 8
        8:  [0, 1, 2, 5, 6, 9, 10, 11],    # Location 9
        9:  [5, 10, 11, 12],               # Location 10
        10: [0, 2, 3, 5, 6, 8],            # Location 11
        11: [0, 2, 4, 7, 8],               # Location 12
        12: [0, 3, 8, 10, 11, 12, 13],     # Location 13
        13: [1, 3, 6, 7, 12],              # Location 14
        14: [4, 6, 7, 8],                  # Location 15
        15: [0, 4, 5, 7, 10, 12],          # Location 16
        16: [0, 3, 4, 5, 7, 13],           # Location 17
        17: [2, 7, 9, 10, 11, 13],         # Location 18
        18: [1, 4, 6, 11, 12],             # Location 19
        19: [0, 2, 3, 4, 9, 10, 12],       # Location 20
        20: [0, 7, 11, 13],                # Location 21
    }

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary decision variables: select team j or not
    x = model.addVars(num_teams, vtype=GRB.BINARY, name="x")

    # Objective: minimize total deployment cost
    model.setObjective(
        gp.quicksum(team_costs[j] * x[j] for j in range(num_teams)),
        GRB.MINIMIZE
    )

    # Coverage constraints: sum of selected teams covering location i >= requirement
    for i in range(num_locations):
        req = location_requirements[i]
        teams_for_location = coverage[i]
        model.addConstr(
            gp.quicksum(x[j] for j in teams_for_location) >= req,
            name=f"cov_{i}"
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