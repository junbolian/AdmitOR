import gurobipy as gp
from gurobipy import GRB

def solve(params):
    activation_cost = params["activation_cost"]

    # Coverage sets: service area (1-indexed) -> list of facilities (1-indexed) that can cover it
    coverage = {
        1:  [1, 2, 3, 4, 5, 7, 9, 10, 11, 13, 14, 17, 18, 21],
        2:  [1, 5, 6, 7, 9, 11, 12, 13, 14, 15, 16, 17, 19, 20],
        3:  [4, 5, 6, 7, 8, 10, 18, 20, 21],
        4:  [4, 5, 6, 9, 10, 11, 13, 14, 16, 17, 18, 19, 20, 21],
        5:  [1, 2, 4, 9, 10, 11, 12, 13, 14, 15, 20],
        6:  [1, 2, 3, 4, 5, 6, 7, 9, 11, 12, 14, 15, 16, 18, 19, 21],
        7:  [4, 5, 9, 10, 12, 14, 16, 17, 18, 20, 21],
        8:  [2, 3, 4, 5, 9, 10, 11, 14, 15, 16, 17, 18, 19, 20],
        9:  [1, 2, 6, 11, 13, 14, 18, 20, 21],
        10: [1, 3, 5, 8, 11, 13, 14, 16, 17, 21],
        11: [1, 2, 3, 7, 8, 9, 10, 12, 15, 16, 17, 18, 19],
        12: [1, 2, 3, 4, 5, 13, 14, 15, 16, 17, 19, 21],
        13: [4, 5, 6, 7, 8, 12, 14, 15, 17, 18, 19, 21],
        14: [1, 2, 4, 5, 7, 9, 10, 11, 16, 17, 20, 21],
        15: [1, 2, 3, 4, 7, 8, 9, 10, 11, 13, 15, 16, 17, 21],
        16: [3, 4, 5, 7, 8, 9, 11, 12, 13, 15, 17, 18, 19, 20, 21],
        17: [4, 7, 10, 11, 12, 14, 15, 16, 17, 18, 19, 21],
        18: [3, 4, 5, 7, 8, 9, 13, 15, 18, 19, 20],
        19: [2, 3, 5, 6, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
        20: [3, 6, 7, 8, 9, 10, 11, 12, 15, 16, 19, 21],
        21: [1, 2, 3, 4, 6, 7, 9, 11, 14, 17, 19],
        22: [1, 2, 4, 5, 6, 8, 10, 11, 14, 17, 18, 19, 20],
        23: [1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 20, 21],
        24: [1, 2, 3, 4, 5, 8, 10, 11, 13, 14, 15, 16, 18, 20, 21],
        25: [2, 3, 8, 9, 10, 11, 13, 14, 15, 17, 18, 20],
        26: [1, 2, 3, 4, 5, 9, 10, 11, 13, 15, 16, 17, 18, 20, 21],
        27: [7, 8, 10, 12, 13, 14, 15, 16, 17, 18, 20],
        28: [4, 7, 8, 10, 11, 13, 14, 16, 17, 20, 21],
        29: [1, 4, 5, 6, 7, 10, 11, 12, 13, 15, 16, 18, 19, 21],
        30: [3, 6, 9, 11, 12, 15, 16, 21],
        31: [1, 3, 4, 10, 13, 14, 15, 18, 19, 21],
        32: [1, 2, 4, 10, 11, 13, 15, 16, 18, 20],
        33: [2, 3, 4, 7, 8, 9, 10, 11, 13, 15, 17, 18, 19, 20, 21],
        34: [1, 4, 11, 12, 13, 14, 15, 16, 18, 20, 21],
        35: [2, 3, 5, 7, 9, 11, 13, 15, 16, 17, 18, 19, 20],
        36: [1, 3, 4, 5, 6, 7, 8, 9, 11, 13, 15, 16, 17, 19, 20, 21],
    }

    num_facilities = 21
    facilities = range(1, num_facilities + 1)

    model = gp.Model("facility_coverage")
    model.setParam("OutputFlag", 0)

    # Binary decision variables: x[f] = 1 if facility f is activated
    x = model.addVars(facilities, vtype=GRB.BINARY, name="x")

    # Objective: minimize total activation cost
    model.setObjective(
        gp.quicksum(activation_cost[f - 1] * x[f] for f in facilities),
        GRB.MINIMIZE
    )

    # Coverage constraints: each service area must be covered by at least one active facility
    for sa, facs in coverage.items():
        model.addConstr(
            gp.quicksum(x[f] for f in facs) >= 1,
            name=f"cover_{sa}"
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