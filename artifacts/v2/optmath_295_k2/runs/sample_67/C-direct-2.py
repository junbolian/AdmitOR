import gurobipy as gp
from gurobipy import GRB

def solve(params):
    hub_activation_costs = params["hub_activation_costs"]

    hubs = list(range(1, 16))
    routes = list(range(1, 17))

    # Which hubs can service each route
    route_hubs = {
        1:  [2, 3, 4, 7, 11, 13],
        2:  [10, 12, 15],
        3:  [1, 5, 6, 8, 11, 12, 13, 14],
        4:  [2, 3, 4, 6, 7, 10, 12, 14],
        5:  [1, 2, 3, 10, 13],
        6:  [1, 2, 3, 6, 8, 10, 11, 12, 14],
        7:  [3, 4, 5, 7, 8, 10, 11, 13, 14],
        8:  [1, 2, 3, 7, 9, 12, 13],
        9:  [1, 4, 7, 10, 12, 13, 14],
        10: [1, 3, 4, 5, 7, 10, 11, 13, 14, 15],
        11: [1, 4, 7, 9, 13, 14],
        12: [3, 4, 6, 8, 10, 11, 12, 13, 14, 15],
        13: [1, 2, 4, 5, 7, 11, 13, 14],
        14: [1, 4, 5, 6, 9, 12, 14, 15],
        15: [2, 6, 7, 12, 13, 14],
        16: [1, 4, 8, 11, 12, 14, 15],
    }

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary activation variables for each hub
    x = {h: model.addVar(vtype=GRB.BINARY, name=f"x_{h}") for h in hubs}

    # Minimize total activation cost
    model.setObjective(
        gp.quicksum(hub_activation_costs[h - 1] * x[h] for h in hubs),
        GRB.MINIMIZE
    )

    # Each route must be covered by at least one active hub
    for r in routes:
        model.addConstr(
            gp.quicksum(x[h] for h in route_hubs[r]) >= 1,
            name=f"cover_route_{r}"
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