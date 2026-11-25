import gurobipy as gp
from gurobipy import GRB

def solve(params):
    facility_open_cost = params["facility_open_cost"]

    num_facilities = 22
    num_zones = 39

    # Coverage: zone -> list of facilities (1-indexed) that can cover it
    coverage = {
        1:  [2, 4, 6, 7, 8, 9, 13, 21],
        2:  [2, 3, 6, 8, 9, 15, 18, 19, 20, 21, 22],
        3:  [1, 3, 5, 6, 8, 17, 18, 19, 20, 22],
        4:  [3, 4, 5, 6, 9, 10, 11, 12, 13, 15, 16, 17, 18, 20],
        5:  [1, 5, 7, 9, 10, 13, 14, 16, 17, 18, 20, 21],
        6:  [1, 2, 3, 4, 5, 7, 9, 10, 16, 17, 19, 20, 21],
        7:  [1, 3, 7, 8, 9, 11, 13, 14, 16, 19, 20, 21, 22],
        8:  [1, 2, 6, 7, 9, 10, 13, 14, 15, 16, 17, 18, 19, 21],
        9:  [1, 2, 3, 7, 8, 10, 13, 14, 15, 16, 18, 21, 22],
        10: [1, 2, 3, 4, 5, 7, 8, 9, 11, 14, 15, 16, 17, 20, 21, 22],
        11: [1, 4, 5, 7, 10, 11, 14, 16, 17, 18, 19, 21],
        12: [1, 2, 4, 5, 8, 10, 11, 13, 14, 15, 16, 17, 18, 21, 22],
        13: [1, 3, 4, 5, 6, 9, 10, 12, 14, 15, 16, 17, 19, 20, 21],
        14: [1, 4, 5, 6, 7, 8, 9, 11, 12, 16, 17, 18, 19, 20],
        15: [1, 2, 6, 7, 8, 9, 10, 11, 15, 16, 17, 20, 22],
        16: [2, 6, 8, 9, 10, 11, 12, 13, 18, 19, 22],
        17: [1, 4, 7, 8, 10, 11, 12, 15, 17, 19, 21],
        18: [1, 3, 4, 5, 7, 8, 9, 11, 12, 14, 15, 16, 17, 18, 19, 20, 21],
        19: [1, 3, 5, 6, 8, 9, 10, 12, 13, 14, 15, 17, 19, 20, 21],
        20: [1, 2, 3, 4, 8, 9, 10, 11, 13, 14, 15, 16, 17, 18, 20, 21],
        21: [1, 2, 3, 6, 8, 9, 11, 12, 14, 18, 20, 21, 22],
        22: [2, 4, 5, 7, 8, 12, 13, 14, 15, 17, 18, 20, 21],
        23: [5, 6, 8, 9, 10, 11, 16, 18, 19, 20, 21, 22],
        24: [6, 11, 14, 16, 17, 18, 20, 21, 22],
        25: [1, 2, 4, 5, 9, 10, 11, 12, 13, 14, 15, 16, 17, 19, 20, 22],
        26: [3, 4, 7, 8, 9, 10, 11, 12, 14, 15, 16, 17, 20, 22],
        27: [1, 3, 4, 6, 7, 10, 12, 13, 15, 16, 19, 20, 21, 22],
        28: [1, 2, 3, 6, 7, 8, 9, 13, 16, 18, 21, 22],
        29: [4, 6, 7, 8, 12, 16, 17, 20, 21, 22],
        30: [2, 5, 6, 7, 8, 9, 11, 13, 14, 15, 16, 17, 18, 19, 20],
        31: [2, 3, 4, 6, 7, 8, 9, 10, 11, 12, 13, 15, 16, 17, 18, 19, 20, 22],
        32: [3, 4, 5, 6, 7, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22],
        33: [3, 4, 5, 7, 10, 12, 13, 16, 18, 19, 20],
        34: [2, 5, 6, 7, 9, 11, 12, 13, 17, 19, 20, 21, 22],
        35: [3, 5, 7, 8, 10, 11, 13, 14, 15, 16, 19, 21, 22],
        36: [1, 4, 8, 9, 10, 11, 16, 18, 20, 21, 22],
        37: [1, 3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 20, 22],
        38: [2, 4, 7, 8, 9, 10, 13, 14, 15, 16, 17, 18, 19, 21],
        39: [3, 4, 5, 6, 7, 9, 13, 14, 15, 16, 17, 18, 20, 22],
    }

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary variable: open facility j (1-indexed stored as 0-indexed here)
    x = model.addVars(range(1, num_facilities + 1), vtype=GRB.BINARY, name="x")

    # Objective: minimize total opening cost
    model.setObjective(
        gp.quicksum(facility_open_cost[j - 1] * x[j] for j in range(1, num_facilities + 1)),
        GRB.MINIMIZE
    )

    # Coverage constraints: each zone must be covered by at least one open facility
    for zone in range(1, num_zones + 1):
        covering = coverage[zone]
        model.addConstr(
            gp.quicksum(x[j] for j in covering) >= 1,
            name=f"cover_zone_{zone}"
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