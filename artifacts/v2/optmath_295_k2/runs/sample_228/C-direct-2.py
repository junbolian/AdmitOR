import gurobipy as gp
from gurobipy import GRB

def solve(params):
    facility_costs = params["facility_costs"]

    # Coverage sets: service area (0-indexed) -> list of facilities (0-indexed) that cover it
    coverage = {
        0:  [1,2,3,4,9,10,11,12,13,14,15,17,21],
        1:  [1,2,3,4,5,7,9,10,11,12,13,14,15,16,17,18,19,21,23,24,25],
        2:  [3,4,7,8,10,11,12,13,14,16,20,22,25],
        3:  [1,2,3,4,6,7,8,9,10,11,12,13,15,16,19,20,22,24,25],
        4:  [2,10,12,14,17,18,19,21,23,24,25],
        5:  [3,4,5,6,7,8,11,12,17,18,25],
        6:  [2,3,4,6,7,10,12,13,14,15,19,20,21,22,25],
        7:  [1,2,3,4,5,6,9,12,13,15,16,17,18,19,20,22,23,24],
        8:  [5,6,7,9,11,12,14,15,21,22,23,24,25],
        9:  [4,7,8,9,10,13,14,15,16,19,21,23,24],
        10: [6,10,12,13,15,18,22,25],
        11: [1,3,5,6,10,11,13,14,15,16,18,19,20,22,24,25],
        12: [4,5,7,10,11,12,13,14,18,19,20,21,25],
        13: [1,4,5,6,7,8,10,15,18,19,20,21,22,23,24,25],
        14: [1,2,3,4,5,7,8,9,10,12,13,16,18,19,20,21,24],
        15: [1,3,5,6,8,11,13,14,18,19,20,21,22,23,24],
        16: [8,9,13,14,15,16,20,21,25],
        17: [1,2,3,4,6,7,8,9,10,12,13,14,15,16,17,18,19,20,21,22,24],
        18: [1,3,4,5,6,7,9,13,14,15,16,18,19,24],
        19: [2,3,6,9,11,15,16,17,19,20,21,25],
        20: [1,2,4,6,7,9,10,11,12,14,15,16,17,18,19,20,21,22,23,24,25],
        21: [1,4,5,6,10,11,12,13,15,16,18,19,21],
        22: [1,2,3,5,6,9,10,13,15,16,17,18,19,20,21,22,24],
        23: [4,5,6,8,10,15,16,17,18,20,25],
        24: [1,3,5,6,9,10,11,12,14,17,18,19,21,22,23,25],
        25: [2,3,4,5,7,8,9,11,13,14,16,19,20,21,22,24,25],
        26: [5,6,8,9,12,14,17,18,19,22,23,25],
        27: [1,3,4,5,6,8,10,14,16,17,19,20,23,24,25],
        28: [2,3,4,6,7,8,9,11,12,14,15,17,18,19,20,21,22,23,24],
        29: [1,2,3,5,10,12,15,16,17,18,20,21,22,25],
        30: [1,2,4,5,6,7,10,11,12,13,14,15,19,20,21,22,24,25],
        31: [1,6,8,9,11,12,13,14,15,16,18,19,20,22,23],
        32: [1,2,4,5,6,7,8,9,14,15,16,17,18,19,20,21,22,24,25],
        33: [1,3,5,6,7,8,9,10,11,12,13,14,15,17,18],
        34: [2,3,5,8,9,10,11,13,15,16,17,19,21,22,24,25],
        35: [2,5,6,7,9,11,12,14,16,20,21,22,24,25],
    }

    num_facilities = 25
    num_service_areas = 36

    model = gp.Model("facility_set_cover")
    model.setParam("OutputFlag", 0)

    # Binary decision variables: x[j] = 1 if facility j is selected (1-indexed)
    x = model.addVars(range(1, num_facilities + 1), vtype=GRB.BINARY, name="x")

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(facility_costs[j - 1] * x[j] for j in range(1, num_facilities + 1)),
        GRB.MINIMIZE
    )

    # Coverage constraints: each service area must be covered by at least one selected facility
    for area_idx in range(num_service_areas):
        covering_facilities = coverage[area_idx]
        model.addConstr(
            gp.quicksum(x[j] for j in covering_facilities) >= 1,
            name=f"cover_{area_idx}"
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