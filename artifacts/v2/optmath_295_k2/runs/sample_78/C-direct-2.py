import gurobipy as gp
from gurobipy import GRB

def solve(params):
    deployment_costs = params["deployment_costs"]
    coverage_requirements = params["coverage_requirements"]

    # Structural team-location coverage (1-based team indices per location 1..18)
    teams_for_location = [
        [4, 8, 10, 11],               # Location 1
        [2, 3, 7, 8, 10],             # Location 2
        [1, 4, 6],                    # Location 3
        [8, 10, 12],                  # Location 4
        [1, 3, 4, 8, 11],             # Location 5
        [1, 2, 6, 7, 8, 12],         # Location 6
        [1, 2, 4, 6, 9, 11],         # Location 7
        [2, 7, 8, 11],               # Location 8
        [2, 3, 4, 6],                # Location 9
        [2, 3, 5, 6, 9, 10, 11, 12], # Location 10
        [2, 3, 4, 10],               # Location 11
        [4, 5, 9, 10, 11],           # Location 12
        [7, 9, 12],                  # Location 13
        [1, 7, 9, 11],               # Location 14
        [6, 7, 8, 9, 10],            # Location 15
        [1, 4, 6, 7, 9, 10, 12],     # Location 16
        [4, 5, 7, 8, 10, 12],        # Location 17
        [1, 5, 8, 9],                # Location 18
    ]

    model = gp.Model("team_deployment")
    model.setParam("OutputFlag", 0)

    x = model.addVars(12, vtype=GRB.BINARY, name="x")

    model.setObjective(
        gp.quicksum(deployment_costs[i] * x[i] for i in range(12)),
        GRB.MINIMIZE,
    )

    for loc_idx in range(18):
        teams = teams_for_location[loc_idx]
        req = coverage_requirements[loc_idx]
        model.addConstr(
            gp.quicksum(x[t - 1] for t in teams) >= req,
            name=f"coverage_loc{loc_idx + 1}",
        )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.objVal), "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"failed_status_{model.status}"}