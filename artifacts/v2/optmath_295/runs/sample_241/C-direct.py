import gurobipy as gp
from gurobipy import GRB

def solve(params):
    program_costs = params["program_costs"]
    num_programs = 17
    num_topics = 37

    # Coverage: topic index (0-based) -> list of program indices (0-based) that cover it
    coverage = {
        0:  [0, 1, 3, 5, 8, 9, 12, 13, 14, 16],
        1:  [3, 4, 6, 7, 12, 16],
        2:  [3, 4, 6, 7, 9, 10, 11, 14, 15, 16],
        3:  [4, 5, 6, 10, 12, 15, 16],
        4:  [1, 2, 3, 5, 7, 8, 9, 15],
        5:  [1, 2, 3, 6, 10, 16],
        6:  [3, 4, 8, 12, 16],
        7:  [0, 3, 5, 6, 7, 9, 11, 12, 14, 16],
        8:  [0, 6, 7, 11, 14, 15],
        9:  [1, 2, 3, 4, 5, 8, 12, 15],
        10: [2, 6, 8, 10, 13, 14],
        11: [4, 6, 9, 11, 13],
        12: [0, 2, 4, 8, 9, 10, 12],
        13: [1, 6, 7, 12, 13, 14, 15],
        14: [1, 4, 7, 12, 15],
        15: [1, 2, 8],
        16: [1, 2, 3, 4, 6, 9, 12, 15],
        17: [2, 5, 6, 7, 8, 14, 15],
        18: [6, 8, 9, 12, 13, 14],
        19: [1, 2, 3, 4, 5, 10, 11, 13, 16],
        20: [0, 1, 6, 8, 11, 13, 15],
        21: [2, 3, 5, 8, 10, 15],
        22: [1, 5, 9, 10, 13],
        23: [0, 2, 5, 6, 10, 11, 12, 14, 15],
        24: [0, 2, 6, 7, 10, 11, 14],
        25: [2, 4, 9, 10, 11, 15],
        26: [5, 6, 8, 9, 10, 11, 15],
        27: [2, 3, 5, 6, 10, 11],
        28: [2, 5, 6, 9, 12, 15, 16],
        29: [1, 5, 8, 9, 12, 14, 15, 16],
        30: [1, 5, 6, 7, 8, 10, 11, 12, 16],
        31: [0, 6, 8, 12, 14],
        32: [0, 2, 5, 8, 12, 13],
        33: [1, 2, 5, 12, 13, 14, 16],
        34: [0, 1, 2, 5, 9, 10, 11, 16],
        35: [3, 4, 6, 11, 12],
        36: [1, 7, 10, 15],
    }

    model = gp.Model("set_cover")
    model.Params.OutputFlag = 0

    x = model.addVars(num_programs, vtype=GRB.BINARY, name="x")

    model.setObjective(
        gp.quicksum(program_costs[j] * x[j] for j in range(num_programs)),
        GRB.MINIMIZE,
    )

    for t in range(num_topics):
        model.addConstr(
            gp.quicksum(x[j] for j in coverage[t]) >= 1,
            name=f"cover_topic_{t}",
        )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}

    if model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}

    return {"objective": None, "status": f"failed_status_{model.status}"}