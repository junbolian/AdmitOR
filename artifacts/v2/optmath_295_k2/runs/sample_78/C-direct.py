import gurobipy as gp
from gurobipy import GRB

def solve(params):
    deployment_costs = params["deployment_costs"]
    coverage_requirements = params["coverage_requirements"]

    # Coverage structure: for each location, which teams can cover it
    # Teams are 1-indexed in the problem; we use 0-indexed internally
    location_teams = [
        [4, 8, 10, 11],           # Location 1
        [2, 3, 7, 8, 10],         # Location 2
        [1, 4, 6],                 # Location 3
        [8, 10, 12],               # Location 4
        [1, 3, 4, 8, 11],         # Location 5
        [1, 2, 6, 7, 8, 12],      # Location 6
        [1, 2, 4, 6, 9, 11],      # Location 7
        [2, 7, 8, 11],             # Location 8
        [2, 3, 4, 6],              # Location 9
        [2, 3, 5, 6, 9, 10, 11, 12], # Location 10
        [2, 3, 4, 10],             # Location 11
        [4, 5, 9, 10, 11],         # Location 12
        [7, 9, 12],                # Location 13
        [1, 7, 9, 11],             # Location 14
        [6, 7, 8, 9, 10],          # Location 15
        [1, 4, 6, 7, 9, 10, 12],  # Location 16
        [4, 5, 7, 8, 10, 12],     # Location 17
        [1, 5, 8, 9],              # Location 18
    ]

    num_teams = 12
    num_locations = 18

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary decision variables: deploy[j] = 1 if team j+1 is deployed
    deploy = model.addVars(num_teams, vtype=GRB.BINARY, name="deploy")

    # Objective: minimize total deployment cost
    model.setObjective(
        gp.quicksum(deployment_costs[j] * deploy[j] for j in range(num_teams)),
        GRB.MINIMIZE
    )

    # Coverage constraints
    for i in range(num_locations):
        teams = location_teams[i]
        req = coverage_requirements[i]
        model.addConstr(
            gp.quicksum(deploy[t - 1] for t in teams) >= req,
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