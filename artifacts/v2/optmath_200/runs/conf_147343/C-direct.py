import gurobipy as gp
from gurobipy import GRB

def solve(params):
    team_costs = params["team_costs"]

    # Coverage sets: zone (1-indexed) -> list of teams (1-indexed) that can cover it
    coverage = {
        1:  [3, 4, 6, 7, 9, 10],
        2:  [1, 2, 3, 7, 11],
        3:  [1, 5, 8, 9, 12, 13],
        4:  [1, 3, 4, 5, 6, 7, 8, 9, 10, 13],
        5:  [1, 2, 8, 9, 10, 11, 12, 13],
        6:  [1, 7, 10, 13],
        7:  [4, 5, 7, 8, 9, 11, 13],
        8:  [2, 3, 6, 8],
        9:  [1, 2, 3, 6, 7, 8, 9, 10, 12, 13],
        10: [1, 2, 3, 7, 8, 10, 11, 12, 13],
        11: [1, 2, 4, 5, 7, 8, 9, 10, 12],
        12: [1, 8, 9, 11, 12, 13],
        13: [2, 3, 4, 5, 6, 7, 10, 13],
        14: [1, 2, 5, 8, 9, 11],
        15: [4, 6, 8, 13],
        16: [1, 2, 3, 4, 6, 8, 10],
        17: [2, 11],
        18: [1, 2, 5, 10, 11, 12],
    }

    num_teams = 13
    num_zones = 18

    model = gp.Model("patrol_coverage")
    model.setParam("OutputFlag", 0)

    # Binary decision variables: x[t] = 1 if team t is selected (1-indexed)
    x = model.addVars(range(1, num_teams + 1), vtype=GRB.BINARY, name="x")

    # Objective: minimize total deployment cost
    model.setObjective(
        gp.quicksum(team_costs[t - 1] * x[t] for t in range(1, num_teams + 1)),
        GRB.MINIMIZE
    )

    # Coverage constraints: each zone must be covered by at least one selected team
    for z in range(1, num_zones + 1):
        model.addConstr(
            gp.quicksum(x[t] for t in coverage[z]) >= 1,
            name=f"zone_{z}"
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