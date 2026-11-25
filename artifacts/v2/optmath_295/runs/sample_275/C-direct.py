import gurobipy as gp
from gurobipy import GRB


def solve(params):
    facility_cost = params["facility_cost"]
    num_facilities = params["num_facilities"]
    num_service_areas = params["num_service_areas"]
    coverage_requirement = params["coverage_requirement"]

    # Coverage sets: for each service area (0-indexed), which facilities (0-indexed) cover it
    coverage = {
        0:  [1,2,3,4,5,7,9,10,11,13,14,17,18,21],
        1:  [1,5,6,7,9,11,12,13,14,15,16,17,19,20],
        2:  [4,5,6,7,8,10,18,20,21],
        3:  [4,5,6,9,10,11,13,14,16,17,18,19,20,21],
        4:  [1,2,4,9,10,11,12,13,14,15,20],
        5:  [1,2,3,4,5,6,7,9,11,12,14,15,16,18,19,21],
        6:  [4,5,9,10,12,14,16,17,18,20,21],
        7:  [2,3,4,5,9,10,11,14,15,16,17,18,19,20],
        8:  [1,2,6,11,13,14,18,20,21],
        9:  [1,3,5,8,11,13,14,16,17,21],
        10: [1,2,3,7,8,9,10,12,15,16,17,18,19],
        11: [1,2,3,4,5,13,14,15,16,17,19,21],
        12: [4,5,6,7,8,12,14,15,17,18,19,21],
        13: [1,2,4,5,7,9,10,11,16,17,20,21],
        14: [1,2,3,4,7,8,9,10,11,13,15,16,17,21],
        15: [3,4,5,7,8,9,11,12,13,15,17,18,19,20,21],
        16: [4,7,10,11,12,14,15,16,17,18,19,21],
        17: [3,4,5,7,8,9,13,15,18,19,20],
        18: [2,3,5,6,8,9,10,11,12,13,14,15,16,17,18,19,20],
        19: [3,6,7,8,9,10,11,12,15,16,19,21],
        20: [1,2,3,4,6,7,9,11,14,17,19],
        21: [1,2,4,5,6,8,10,11,14,17,18,19,20],
        22: [1,2,3,4,6,7,8,9,10,11,12,13,14,15,20,21],
        23: [1,2,3,4,5,8,10,11,13,14,15,16,18,20,21],
        24: [2,3,8,9,10,11,13,14,15,17,18,20],
        25: [1,2,3,4,5,9,10,11,13,15,16,17,18,20,21],
        26: [7,8,10,12,13,14,15,16,17,18,20],
        27: [4,7,8,10,11,13,14,16,17,20,21],
        28: [1,4,5,6,7,10,11,12,13,15,16,18,19,21],
        29: [3,6,9,11,12,15,16,21],
        30: [1,3,4,10,13,14,15,18,19,21],
        31: [1,2,4,10,11,13,15,16,18,20],
        32: [2,3,4,7,8,9,10,11,13,15,17,18,19,20,21],
        33: [1,4,11,12,13,14,15,16,18,20,21],
        34: [2,3,5,7,9,11,13,15,16,17,18,19,20],
        35: [1,3,4,5,6,7,8,9,11,13,15,16,17,19,20,21],
    }

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary decision variables: x[f] = 1 if facility f is activated (1-indexed)
    x = model.addVars(range(1, num_facilities + 1), vtype=GRB.BINARY, name="x")

    # Objective: minimize total activation cost
    model.setObjective(
        gp.quicksum(facility_cost[f - 1] * x[f] for f in range(1, num_facilities + 1)),
        GRB.MINIMIZE
    )

    # Coverage constraints: for each service area, sum of active covering facilities >= requirement
    for sa in range(num_service_areas):
        covering = coverage[sa]
        req = coverage_requirement[sa] if isinstance(coverage_requirement, list) else coverage_requirement
        model.addConstr(
            gp.quicksum(x[f] for f in covering) >= req,
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