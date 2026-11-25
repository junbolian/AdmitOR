import gurobipy as gp
from gurobipy import GRB

def solve(params):
    team_costs = params["team_costs"]

    # Coverage sets: location -> list of teams (1-indexed) that can cover it
    coverage = {
        1:  [1, 2, 4, 5, 6, 7, 9],
        2:  [1, 3, 4, 5, 6, 9, 10],
        3:  [1, 2, 3, 4, 8, 10],
        4:  [2, 5, 8, 10],
        5:  [1, 7],
        6:  [1, 2, 3, 5, 8, 9, 10],
        7:  [1, 2, 4, 5, 9],
        8:  [3, 8, 9],
        9:  [3, 4, 5, 7],
        10: [1, 2, 5, 6],
        11: [2, 3, 7, 9],
        12: [5, 7, 8, 9, 10],
        13: [2, 3, 8, 10],
        14: [1, 2, 3, 5, 6, 9, 10],
        15: [2, 6, 8, 9],
        16: [2, 3, 5, 7, 10],
        17: [1, 2, 3, 5, 8, 9, 10],
    }

    num_teams = 10
    teams = range(1, num_teams + 1)
    locations = range(1, 18)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary decision variables: deploy team t or not
    x = model.addVars(teams, vtype=GRB.BINARY, name="x")

    # Objective: minimize total deployment cost
    model.setObjective(
        gp.quicksum(team_costs[t - 1] * x[t] for t in teams),
        GRB.MINIMIZE
    )

    # Coverage constraints: each location covered by at least one deployed team
    for loc in locations:
        model.addConstr(
            gp.quicksum(x[t] for t in coverage[loc]) >= 1,
            name=f"cover_{loc}"
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