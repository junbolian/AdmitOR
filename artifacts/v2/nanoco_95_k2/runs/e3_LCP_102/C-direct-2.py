import gurobipy as gp
from gurobipy import GRB


def solve(params):
    zones = list(range(10))

    permitted = {
        0: {0, 1, 2, 4, 5, 6, 7, 8, 9},
        1: {0, 1, 2, 3, 4, 5},
        2: {0, 1, 4, 5, 6, 7, 8},
        3: {0, 2, 3, 4, 7},
        4: {0, 1, 2, 4, 6, 7, 8, 9},
        5: {2, 3, 4, 6, 7},
        6: {0, 2, 3, 4, 5, 6, 8},
        7: {0, 1, 2, 3, 4, 5, 6, 7, 8, 9},
        8: {0, 1, 2, 3, 4, 5, 6, 7, 8, 9},
        9: {0, 2, 3, 5, 8, 9},
    }

    incompat = [
        (0, 1), (0, 4), (3, 4), (5, 7), (0, 6),
        (3, 9), (0, 5), (0, 8), (1, 3), (7, 8),
    ]

    max_type = max(max(permitted[i]) for i in zones)

    model = gp.Model("warehouse_zones")
    model.Params.OutputFlag = 0

    # x[i, t] = 1 if zone i is assigned storage zone type t
    x = {}
    for i in zones:
        for t in permitted[i]:
            x[i, t] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{t}")

    # y = maximum storage zone type index used
    y = model.addVar(lb=0, ub=max_type, vtype=GRB.INTEGER, name="y")

    model.update()

    # Each zone assigned exactly one type from its permitted list
    for i in zones:
        model.addConstr(
            gp.quicksum(x[i, t] for t in permitted[i]) == 1,
            name=f"assign_{i}",
        )

    # Incompatible zones cannot share the same type
    for (i, j) in incompat:
        common = permitted[i] & permitted[j]
        for t in common:
            model.addConstr(
                x[i, t] + x[j, t] <= 1,
                name=f"incompat_{i}_{j}_{t}",
            )

    # Link y to the maximum assigned type: if x[i, t] = 1 then y >= t
    for i in zones:
        for t in permitted[i]:
            model.addConstr(y >= t * x[i, t], name=f"link_{i}_{t}")

    model.setObjective(y, GRB.MINIMIZE)
    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.objVal), "status": "optimal"}

    if model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}

    return {"objective": None, "status": "failed"}