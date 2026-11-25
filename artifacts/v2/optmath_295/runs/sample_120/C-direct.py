import gurobipy as gp
from gurobipy import GRB

def solve(params):
    facility_cost = params["facility_cost"]

    num_facilities = 22
    num_zones = 39

    # Coverage: zone (0-indexed) -> list of facilities (0-indexed) that can cover it
    coverage = {
        0:  [2,4,6,7,8,9,13,21],
        1:  [2,3,6,8,9,15,18,19,20,21,22],
        2:  [1,3,5,6,8,17,18,19,20,22],
        3:  [3,4,5,6,9,10,11,12,13,15,16,17,18,20],
        4:  [1,5,7,9,10,13,14,16,17,18,20,21],
        5:  [1,2,3,4,5,7,9,10,16,17,19,20,21],
        6:  [1,3,7,8,9,11,13,14,16,19,20,21,22],
        7:  [1,2,6,7,9,10,13,14,15,16,17,18,19,21],
        8:  [1,2,3,7,8,10,13,14,15,16,18,21,22],
        9:  [1,2,3,4,5,7,8,9,11,14,15,16,17,20,21,22],
        10: [1,4,5,7,10,11,14,16,17,18,19,21],
        11: [1,2,4,5,8,10,11,13,14,15,16,17,18,21,22],
        12: [1,3,4,5,6,9,10,12,14,15,16,17,19,20,21],
        13: [1,4,5,6,7,8,9,11,12,16,17,18,19,20],
        14: [1,2,6,7,8,9,10,11,15,16,17,20,22],
        15: [2,6,8,9,10,11,12,13,18,19,22],
        16: [1,4,7,8,10,11,12,15,17,19,21],
        17: [1,3,4,5,7,8,9,11,12,14,15,16,17,18,19,20,21],
        18: [1,3,5,6,8,9,10,12,13,14,15,17,19,20,21],
        19: [1,2,3,4,8,9,10,11,13,14,15,16,17,18,20,21],
        20: [1,2,3,6,8,9,11,12,14,18,20,21,22],
        21: [2,4,5,7,8,12,13,14,15,17,18,20,21],
        22: [5,6,8,9,10,11,16,18,19,20,21,22],
        23: [6,11,14,16,17,18,20,21,22],
        24: [1,2,4,5,9,10,11,12,13,14,15,16,17,19,20,22],
        25: [3,4,7,8,9,10,11,12,14,15,16,17,20,22],
        26: [1,3,4,6,7,10,12,13,15,16,19,20,21,22],
        27: [1,2,3,6,7,8,9,13,16,18,21,22],
        28: [4,6,7,8,12,16,17,20,21,22],
        29: [2,5,6,7,8,9,11,13,14,15,16,17,18,19,20],
        30: [2,3,4,6,7,8,9,10,11,12,13,15,16,17,18,19,20,22],
        31: [3,4,5,6,7,13,14,15,16,17,18,19,20,21,22],
        32: [3,4,5,7,10,12,13,16,18,19,20],
        33: [2,5,6,7,9,11,12,13,17,19,20,21,22],
        34: [3,5,7,8,10,11,13,14,15,16,19,21,22],
        35: [1,4,8,9,10,11,16,18,20,21,22],
        36: [1,3,5,6,7,8,9,10,11,12,13,14,20,22],
        37: [2,4,7,8,9,10,13,14,15,16,17,18,19,21],
        38: [3,4,5,6,7,9,13,14,15,16,17,18,20,22],
    }

    # Convert 1-indexed facility lists to 0-indexed
    coverage_0 = {z: [f - 1 for f in facs] for z, facs in coverage.items()}

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary decision variables: open facility i or not
    x = model.addVars(num_facilities, vtype=GRB.BINARY, name="x")

    # Objective: minimize total facility cost
    model.setObjective(
        gp.quicksum(facility_cost[i] * x[i] for i in range(num_facilities)),
        GRB.MINIMIZE
    )

    # Coverage constraints: each zone must be covered by at least one open facility
    for z in range(num_zones):
        model.addConstr(
            gp.quicksum(x[f] for f in coverage_0[z]) >= 1,
            name=f"cover_zone_{z}"
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