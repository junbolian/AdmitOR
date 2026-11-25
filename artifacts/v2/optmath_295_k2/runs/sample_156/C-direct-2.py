import gurobipy as gp
from gurobipy import GRB


def solve(params):
    team_costs = params["team_costs"]            # list of 13 costs (Team 1..Team 13)
    area_requirements = params["area_requirements"]  # list of 17 required counts (Area 1..Area 17)

    # Structural coverage: area (1-based) -> list of teams (1-based) that can cover it
    coverage = {
        1: [5, 7, 11],
        2: [1, 2, 5, 9, 11],
        3: [4, 6],
        4: [2, 5, 8, 10, 11],
        5: [2, 6, 7, 9, 10],
        6: [1, 7, 8, 12],
        7: [3, 5, 13],
        8: [2, 7, 9, 12, 13],
        9: [13],
        10: [2, 5, 6, 7, 9, 12],
        11: [2, 3, 6, 7, 8, 10, 11],
        12: [6, 11],
        13: [2, 3, 12],
        14: [6, 10, 11, 12],
        15: [4, 5, 9, 11],
        16: [3, 5, 9, 12, 13],
        17: [5, 7, 8],
    }

    num_teams = 13
    num_areas = 17

    model = gp.Model("emergency_response")
    model.Params.OutputFlag = 0

    # x[t] = 1 if team (t+1) is selected
    x = model.addVars(num_teams, vtype=GRB.BINARY, name="x")

    # Objective: minimize total deployment cost
    model.setObjective(
        gp.quicksum(team_costs[t] * x[t] for t in range(num_teams)),
        GRB.MINIMIZE,
    )

    # Coverage constraints: each area must be covered by at least its required count
    for a in range(num_areas):
        area_id = a + 1
        teams_covering = coverage[area_id]
        req = area_requirements[a]
        model.addConstr(
            gp.quicksum(x[t - 1] for t in teams_covering) >= req,
            name=f"cover_area_{area_id}",
        )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": "no_solution"}