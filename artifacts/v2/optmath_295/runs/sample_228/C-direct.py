import gurobipy as gp
from gurobipy import GRB

def solve(params):
    facility_costs = params["facility_costs"]
    num_facilities = params["num_facilities"]
    num_service_areas = params["num_service_areas"]

    # Coverage sets: for each service area (1-indexed), which facilities cover it
    coverage = {
        1:  [1, 2, 3, 4, 9, 10, 11, 12, 13, 14, 15, 17, 21],
        2:  [1, 2, 3, 4, 5, 7, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 21, 23, 24, 25],
        3:  [3, 4, 7, 8, 10, 11, 12, 13, 14, 16, 20, 22, 25],
        4:  [1, 2, 3, 4, 6, 7, 8, 9, 10, 11, 12, 13, 15, 16, 19, 20, 22, 24, 25],
        5:  [2, 10, 12, 14, 17, 18, 19, 21, 23, 24, 25],
        6:  [3, 4, 5, 6, 7, 8, 11, 12, 17, 18, 25],
        7:  [2, 3, 4, 6, 7, 10, 12, 13, 14, 15, 19, 20, 21, 22, 25],
        8:  [1, 2, 3, 4, 5, 6, 9, 12, 13, 15, 16, 17, 18, 19, 20, 22, 23, 24],
        9:  [5, 6, 7, 9, 11, 12, 14, 15, 21, 22, 23, 24, 25],
        10: [4, 7, 8, 9, 10, 13, 14, 15, 16, 19, 21, 23, 24],
        11: [6, 10, 12, 13, 15, 18, 22, 25],
        12: [1, 3, 5, 6, 10, 11, 13, 14, 15, 16, 18, 19, 20, 22, 24, 25],
        13: [4, 5, 7, 10, 11, 12, 13, 14, 18, 19, 20, 21, 25],
        14: [1, 4, 5, 6, 7, 8, 10, 15, 18, 19, 20, 21, 22, 23, 24, 25],
        15: [1, 2, 3, 4, 5, 7, 8, 9, 10, 12, 13, 16, 18, 19, 20, 21, 24],
        16: [1, 3, 5, 6, 8, 11, 13, 14, 18, 19, 20, 21, 22, 23, 24],
        17: [8, 9, 13, 14, 15, 16, 20, 21, 25],
        18: [1, 2, 3, 4, 6, 7, 8, 9, 10, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 24],
        19: [1, 3, 4, 5, 6, 7, 9, 13, 14, 15, 16, 18, 19, 24],
        20: [2, 3, 6, 9, 11, 15, 16, 17, 19, 20, 21, 25],
        21: [1, 2, 4, 6, 7, 9, 10, 11, 12, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25],
        22: [1, 4, 5, 6, 10, 11, 12, 13, 15, 16, 18, 19, 21],
        23: [1, 2, 3, 5, 6, 9, 10, 13, 15, 16, 17, 18, 19, 20, 21, 22, 24],
        24: [4, 5, 6, 8, 10, 15, 16, 17, 18, 20, 25],
        25: [1, 3, 5, 6, 9, 10, 11, 12, 14, 17, 18, 19, 21, 22, 23, 25],
        26: [2, 3, 4, 5, 7, 8, 9, 11, 13, 14, 16, 19, 20, 21, 22, 24, 25],
        27: [5, 6, 8, 9, 12, 14, 17, 18, 19, 22, 23, 25],
        28: [1, 3, 4, 5, 6, 8, 10, 14, 16, 17, 19, 20, 23, 24, 25],
        29: [2, 3, 4, 6, 7, 8, 9, 11, 12, 14, 15, 17, 18, 19, 20, 21, 22, 23, 24],
        30: [1, 2, 3, 5, 10, 12, 15, 16, 17, 18, 20, 21, 22, 25],
        31: [1, 2, 4, 5, 6, 7, 10, 11, 12, 13, 14, 15, 19, 20, 21, 22, 24, 25],
        32: [1, 6, 8, 9, 11, 12, 13, 14, 15, 16, 18, 19, 20, 22, 23],
        33: [1, 2, 4, 5, 6, 7, 8, 9, 14, 15, 16, 17, 18, 19, 20, 21, 22, 24, 25],
        34: [1, 3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 17, 18],
        35: [2, 3, 5, 8, 9, 10, 11, 13, 15, 16, 17, 19, 21, 22, 24, 25],
        36: [2, 5, 6, 7, 9, 11, 12, 14, 16, 20, 21, 22, 24, 25],
    }

    facilities = range(1, num_facilities + 1)
    service_areas = range(1, num_service_areas + 1)

    model = gp.Model("facility_coverage")
    model.setParam("OutputFlag", 0)

    # Binary decision variables: select facility j or not
    x = model.addVars(facilities, vtype=GRB.BINARY, name="x")

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(facility_costs[j - 1] * x[j] for j in facilities),
        GRB.MINIMIZE
    )

    # Coverage constraints: each service area must be covered by at least one selected facility
    for sa in service_areas:
        covering = coverage[sa]
        model.addConstr(
            gp.quicksum(x[j] for j in covering) >= 1,
            name=f"cover_{sa}"
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
        return {"objective": None, "status": f"solver_status_{status}"}