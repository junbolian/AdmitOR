import gurobipy as gp
from gurobipy import GRB

def solve(params):
    team_costs = params["team_costs"]

    # Coverage sets: location index (0-based) -> list of team indices (0-based)
    coverage = {
        0:  [0, 1, 3, 4, 5, 6, 8],
        1:  [0, 2, 3, 4, 5, 8, 9],
        2:  [0, 1, 2, 3, 7, 9],
        3:  [1, 4, 7, 9],
        4:  [0, 6],
        5:  [0, 1, 2, 4, 7, 8, 9],
        6:  [0, 1, 3, 4, 8],
        7:  [2, 7, 8],
        8:  [2, 3, 4, 6],
        9:  [0, 1, 4, 5],
        10: [1, 2, 6, 8],
        11: [4, 6, 7, 8, 9],
        12: [1, 2, 7, 9],
        13: [0, 1, 2, 4, 5, 8, 9],
        14: [1, 5, 7, 8],
        15: [1, 2, 4, 6, 9],
        16: [0, 1, 2, 4, 7, 8, 9],
    }

    num_teams = 10
    num_locations = 17

    model = gp.Model("emergency_coverage")
    model.setParam("OutputFlag", 0)

    x = model.addVars(num_teams, vtype=GRB.BINARY, name="x")

    model.setObjective(
        gp.quicksum(team_costs[t] * x[t] for t in range(num_teams)),
        GRB.MINIMIZE
    )

    for loc in range(num_locations):
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
        return {"objective": None, "status": f"gurobi_status_{model.Status}"}