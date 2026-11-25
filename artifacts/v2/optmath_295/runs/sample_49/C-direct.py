import gurobipy as gp
from gurobipy import GRB

def solve(params):
    team_costs = params["team_costs"]

    location_requirements = [
        params["location_1_requirement"],
        params["location_2_requirement"],
        params["location_3_requirement"],
        params["location_4_requirement"],
        params["location_5_requirement"],
        params["location_6_requirement"],
        params["location_7_requirement"],
        params["location_8_requirement"],
        params["location_9_requirement"],
        params["location_10_requirement"],
        params["location_11_requirement"],
        params["location_12_requirement"],
        params["location_13_requirement"],
        params["location_14_requirement"],
        params["location_15_requirement"],
        params["location_16_requirement"],
        params["location_17_requirement"],
        params["location_18_requirement"],
        params["location_19_requirement"],
        params["location_20_requirement"],
        params["location_21_requirement"],
    ]

    # coverage_sets[i] = list of team indices (0-based) that can cover location i+1
    coverage_sets = [
        [1, 4, 5, 6, 7, 8, 10, 13],   # location 1: teams 2,5,6,7,8,9,11,14
        [1, 4, 6, 12],                  # location 2: teams 2,5,7,13
        [0, 1, 3, 4, 5, 8, 9, 11, 12], # location 3: teams 1,2,4,5,6,9,10,12,13
        [2, 5, 12, 13],                 # location 4: teams 3,6,13,14
        [1, 5, 9],                      # location 5: teams 2,6,10
        [3, 5, 7, 13],                  # location 6: teams 4,6,8,14
        [0, 3, 4, 7, 9, 10, 11, 12, 13], # location 7: teams 1,4,5,8,10,11,12,13,14
        [0, 4, 10, 13],                 # location 8: teams 1,5,11,14
        [0, 1, 2, 5, 6, 9, 10, 11],    # location 9: teams 1,2,3,6,7,10,11,12
        [5, 10, 11, 12],                # location 10: teams 6,11,12,13
        [0, 2, 3, 5, 6, 8],            # location 11: teams 1,3,4,6,7,9
        [0, 2, 4, 7, 8],               # location 12: teams 1,3,5,8,9
        [0, 3, 8, 10, 11, 12, 13],     # location 13: teams 1,4,9,11,12,13,14
        [1, 3, 6, 7, 12],              # location 14: teams 2,4,7,8,13
        [4, 6, 7, 8],                  # location 15: teams 5,7,8,9
        [0, 4, 5, 7, 10, 12],          # location 16: teams 1,5,6,8,11,13
        [0, 3, 4, 5, 7, 13],           # location 17: teams 1,4,5,6,8,14
        [2, 7, 9, 10, 11, 13],         # location 18: teams 3,8,10,11,12,14
        [1, 4, 6, 11, 12],             # location 19: teams 2,5,7,12,13
        [0, 2, 3, 4, 9, 10, 12],       # location 20: teams 1,3,4,5,10,11,13
        [0, 7, 11, 13],                # location 21: teams 1,8,12,14
    ]

    num_teams = 14
    num_locations = 21

    model = gp.Model("team_deployment")
    model.setParam("OutputFlag", 0)

    x = model.addVars(num_teams, vtype=GRB.BINARY, name="x")

    model.setObjective(
        gp.quicksum(team_costs[t] * x[t] for t in range(num_teams)),
        GRB.MINIMIZE
    )

    for loc in range(num_locations):
        teams_for_loc = coverage_sets[loc]
        req = location_requirements[loc]
        model.addConstr(
            gp.quicksum(x[t] for t in teams_for_loc) >= req,
            name=f"cov_{loc+1}"
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