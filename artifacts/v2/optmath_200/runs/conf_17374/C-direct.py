import gurobipy as gp
from gurobipy import GRB

def solve(params):
    team_costs = {i: params[f"team_cost_{i}"] for i in range(1, 15)}

    coverage_groups = {
        1:  [4, 5, 9, 12, 13, 14],
        2:  [4, 5, 8],
        3:  [1, 4, 8, 10, 12],
        4:  [3, 7, 8, 11, 12, 14],
        5:  [4, 5, 9, 14],
        6:  [4, 5, 9, 10, 11, 12, 13],
        7:  [2, 4, 6, 7, 11],
        8:  [1, 4, 6, 7, 11, 12],
        9:  [1, 3, 5, 6, 7, 12],
        10: [1, 7, 8, 9, 10, 13],
        11: [1, 5, 7, 10, 13, 14],
        12: [1, 2, 8, 10, 12, 13, 14],
        13: [4, 5, 6, 7, 8, 11],
        14: [1, 3, 6, 7, 10],
        15: [3, 4, 9, 12, 13, 14],
        16: [1, 2, 3, 8, 10, 11],
        17: [1, 2, 3, 4, 13],
        18: [1, 2, 3, 7, 12, 14],
        19: [1, 2, 3, 5, 7, 9, 12],
    }

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(range(1, 15), vtype=GRB.BINARY, name="x")

    model.setObjective(
        gp.quicksum(team_costs[i] * x[i] for i in range(1, 15)),
        GRB.MINIMIZE
    )

    for req_idx, members in coverage_groups.items():
        rhs = params[f"coverage_req_{req_idx}"]
        model.addConstr(
            gp.quicksum(x[j] for j in members) >= rhs,
            name=f"cov_{req_idx}"
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