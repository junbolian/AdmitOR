import gurobipy as gp
from gurobipy import GRB

def solve(params):
    team_cost = params["team_cost"]
    area_requirement = params["area_requirement"]

    # Coverage structure: area -> list of teams (1-indexed) that can cover it
    coverage = {
        1:  [5, 7, 11],
        2:  [1, 2, 5, 9, 11],
        3:  [4, 6],
        4:  [2, 5, 8, 10, 11],
        5:  [2, 6, 7, 9, 10],
        6:  [1, 7, 8, 12],
        7:  [3, 5, 13],
        8:  [2, 7, 9, 12, 13],
        9:  [13],
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

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary decision variables: select team t (1-indexed)
    x = model.addVars(range(1, num_teams + 1), vtype=GRB.BINARY, name="x")

    # Objective: minimize total deployment cost
    model.setObjective(
        gp.quicksum(team_cost[t - 1] * x[t] for t in range(1, num_teams + 1)),
        GRB.MINIMIZE
    )

    # Coverage constraints
    for a in range(1, num_areas + 1):
        teams_for_area = coverage[a]
        req = area_requirement[a - 1]
        model.addConstr(
            gp.quicksum(x[t] for t in teams_for_area) >= req,
            name=f"cover_area_{a}"
        )

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"gurobi_status_{status}"}