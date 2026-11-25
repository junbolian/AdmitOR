import gurobipy as gp
from gurobipy import GRB

def solve(params):
    strategy_costs = params["strategy_costs"]

    # Coverage: segment index (0-based) -> list of strategy indices (0-based)
    coverage = {
        0:  [0, 1, 2, 3, 6],
        1:  [0, 2, 4, 5, 6, 7],
        2:  [1, 2, 3, 4, 6],
        3:  [4, 5],
        4:  [1, 2, 4, 6, 7],
        5:  [2, 5, 6, 7],
        6:  [6],
        7:  [3, 7],
        8:  [1, 2, 5, 7],
        9:  [1, 3, 6],
        10: [4, 5],
        11: [0, 1, 3, 6],
        12: [1, 2, 3, 5, 7],
        13: [0, 1, 2, 6],
        14: [4, 5],
        15: [0, 1, 2, 4, 5, 6, 7],
        16: [6],
        17: [0, 3, 5],
        18: [1, 4, 6],
        19: [2, 5],
        20: [0, 3, 4, 5],
        21: [1, 4, 5, 7],
        22: [0, 7],
        23: [3, 4, 5, 7],
        24: [0],
        25: [0, 1, 3, 7],
        26: [6],
        27: [1, 3],
        28: [0, 1, 3, 5],
        29: [6, 7],
        30: [2, 3],
        31: [4, 7],
        32: [3, 5],
        33: [2, 4, 6],
        34: [2, 4, 5],
        35: [0, 2, 3, 4],
        36: [1],
        37: [0, 1, 5],
        38: [0, 1, 2, 3, 6, 7],
    }

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary decision variables: select strategy i or not
    x = model.addVars(8, vtype=GRB.BINARY, name="x")

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(strategy_costs[i] * x[i] for i in range(8)),
        GRB.MINIMIZE
    )

    # Coverage constraints: each segment must be covered by at least one selected strategy
    for seg, strategies in coverage.items():
        model.addConstr(
            gp.quicksum(x[s] for s in strategies) >= 1,
            name=f"seg_{seg}"
        )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}