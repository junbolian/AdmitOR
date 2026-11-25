import gurobipy as gp
from gurobipy import GRB

def solve(params):
    zones = list(range(10))
    all_types = list(range(10))

    permitted = {
        0: [0, 1, 2, 4, 5, 6, 7, 8, 9],
        1: [0, 1, 2, 3, 4, 5],
        2: [0, 1, 4, 5, 6, 7, 8],
        3: [0, 2, 3, 4, 7],
        4: [0, 1, 2, 4, 6, 7, 8, 9],
        5: [2, 3, 4, 6, 7],
        6: [0, 2, 3, 4, 5, 6, 8],
        7: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        8: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
        9: [0, 2, 3, 5, 8, 9],
    }

    incompatible = [
        (0, 1), (0, 4), (3, 4), (5, 7), (0, 6),
        (3, 9), (0, 5), (0, 8), (1, 3), (7, 8),
    ]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[z, t] = 1 if zone z is assigned type t
    x = {}
    for z in zones:
        for t in permitted[z]:
            x[z, t] = model.addVar(vtype=GRB.BINARY, name=f"x_{z}_{t}")

    # max_type: the maximum type index used
    max_type = model.addVar(vtype=GRB.INTEGER, lb=0, ub=9, name="max_type")

    model.setObjective(max_type, GRB.MINIMIZE)

    # Each zone assigned exactly one type
    for z in zones:
        model.addConstr(
            gp.quicksum(x[z, t] for t in permitted[z]) == 1,
            name=f"assign_{z}"
        )

    # max_type >= type index used by each zone
    for z in zones:
        model.addConstr(
            gp.quicksum(t * x[z, t] for t in permitted[z]) <= max_type,
            name=f"max_bound_{z}"
        )

    # Incompatibility: zones in a pair cannot share the same type
    for (z1, z2) in incompatible:
        shared = set(permitted[z1]) & set(permitted[z2])
        for t in shared:
            model.addConstr(
                x[z1, t] + x[z2, t] <= 1,
                name=f"incompat_{z1}_{z2}_{t}"
            )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}