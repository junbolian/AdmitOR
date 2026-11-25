import gurobipy as gp
from gurobipy import GRB

def solve(params):
    team_costs = params["team_costs"]
    task_requirements = params["task_requirements"]
    num_teams = params["num_teams"]
    num_tasks = params["num_tasks"]

    # Coverage structure: which teams (0-indexed) cover each task (0-indexed)
    coverage = {
        0: [3, 4, 6, 7, 9, 11, 12, 13],
        1: [1, 2, 6, 8, 9, 12, 13],
        2: [2, 4, 5, 6, 10, 11],
        3: [0, 1, 3, 5, 7, 8, 9, 12],
        4: [1, 3, 5, 6, 7, 9, 12, 14],
        5: [2, 6, 7, 9, 10, 14],
        6: [0, 2, 8, 9, 11, 13],
        7: [4, 5, 7, 13, 14],
        8: [0, 1, 8, 9, 13],
        9: [2, 6, 10, 11, 12],
        10: [0, 3, 7, 10, 11, 12, 13, 14],
        11: [1, 4, 14],
        12: [1, 3, 8, 10, 12, 14],
        13: [2, 7, 8, 10, 11, 14],
        14: [2, 5, 6, 8, 11, 14],
        15: [9, 12, 14],
    }

    model = gp.Model("team_selection")
    model.Params.OutputFlag = 0

    x = model.addVars(num_teams, vtype=GRB.BINARY, name="x")

    model.setObjective(
        gp.quicksum(team_costs[t] * x[t] for t in range(num_teams)),
        GRB.MINIMIZE,
    )

    for j in range(num_tasks):
        model.addConstr(
            gp.quicksum(x[t] for t in coverage[j]) >= task_requirements[j],
            name=f"cover_{j}",
        )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.objVal), "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"failed_status_{model.status}"}