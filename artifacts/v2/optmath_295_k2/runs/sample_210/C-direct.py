import gurobipy as gp
from gurobipy import GRB

def solve(params):
    setup_costs = {
        1:  params["setup_cost_1"],
        2:  params["setup_cost_2"],
        3:  params["setup_cost_3"],
        4:  params["setup_cost_4"],
        5:  params["setup_cost_5"],
        6:  params["setup_cost_6"],
        7:  params["setup_cost_7"],
        8:  params["setup_cost_8"],
        9:  params["setup_cost_9"],
        10: params["setup_cost_10"],
        11: params["setup_cost_11"],
        12: params["setup_cost_12"],
        13: params["setup_cost_13"],
    }

    coverage = {
        1:  [1, 2, 4, 6, 7, 8, 11],
        2:  [3, 4, 5, 6, 7, 9, 11, 13],
        3:  [1, 3, 4, 5, 7, 8, 9, 10, 11],
        4:  [1, 4, 8, 10, 13],
        5:  [1, 2, 4, 6, 9, 10],
        6:  [3, 4, 5, 6, 7, 8, 10, 13],
        7:  [2, 4, 5, 6, 7, 9, 10, 11, 12, 13],
        8:  [5, 8, 11, 12],
        9:  [1, 3, 4, 7, 8, 10, 12, 13],
        10: [2, 4, 6, 8, 11, 12],
        11: [3, 4, 8, 9, 11],
        12: [2, 4, 5, 7, 11, 12],
        13: [1, 2, 3, 5, 7, 9, 10, 13],
        14: [1, 2, 6, 8, 9, 10, 12, 13],
        15: [1, 3, 5, 10],
        16: [1, 5, 6, 8, 13],
        17: [1, 2, 3, 4, 5, 6, 8, 9, 12],
        18: [1, 4, 6, 9, 11, 13],
        19: [4, 6, 8],
        20: [1, 2, 3, 4, 5, 11, 13],
        21: [2, 3, 6, 9],
    }

    locations = range(1, 14)
    zones = range(1, 22)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(locations, vtype=GRB.BINARY, name="x")

    model.setObjective(
        gp.quicksum(setup_costs[loc] * x[loc] for loc in locations),
        GRB.MINIMIZE
    )

    for zone in zones:
        model.addConstr(
            gp.quicksum(x[loc] for loc in coverage[zone]) >= 1,
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
        return {"objective": None, "status": f"status_{model.Status}"}