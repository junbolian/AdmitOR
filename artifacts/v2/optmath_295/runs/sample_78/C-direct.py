import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost = params["cost"]
    req = params["req"]

    # Coverage sets: location index (0-based) -> list of team indices (0-based)
    coverage = {
        0:  [3, 7, 9, 10],
        1:  [1, 2, 6, 7, 9],
        2:  [0, 3, 5],
        3:  [7, 9, 11],
        4:  [0, 2, 3, 7, 10],
        5:  [0, 1, 5, 6, 7, 11],
        6:  [0, 1, 3, 5, 8, 10],
        7:  [1, 6, 7, 10],
        8:  [1, 2, 3, 5],
        9:  [1, 2, 4, 5, 8, 9, 10, 11],
        10: [1, 2, 3, 9],
        11: [3, 4, 8, 9, 10],
        12: [6, 8, 11],
        13: [0, 6, 8, 10],
        14: [5, 6, 7, 8, 9],
        15: [0, 3, 5, 6, 8, 9, 11],
        16: [3, 4, 6, 7, 9, 11],
        17: [0, 4, 7, 8],
    }

    n_teams = 12
    n_locs = 18

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(n_teams, vtype=GRB.BINARY, name="x")

    model.setObjective(gp.quicksum(cost[t] * x[t] for t in range(n_teams)), GRB.MINIMIZE)

    for loc in range(n_locs):
        teams = coverage[loc]
        model.addConstr(
            gp.quicksum(x[t] for t in teams) >= req[loc],
            name=f"cov_{loc}"
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