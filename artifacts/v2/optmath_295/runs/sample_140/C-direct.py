import gurobipy as gp
from gurobipy import GRB


def solve(params):
    assignment_value = params["assignment_value"]

    pref = [[0] * 6 for _ in range(6)]
    pref[0][5] = params["pref_p0_c5"]
    pref[1][2] = params["pref_p1_c2"]
    pref[1][3] = params["pref_p1_c3"]
    pref[2][4] = params["pref_p2_c4"]
    pz3 = params["pref_zero_p3"]
    pz4 = params["pref_zero_p4"]
    pz5 = params["pref_zero_p5"]
    for c in range(6):
        pref[3][c] = pz3
        pref[4][c] = pz4
        pref[5][c] = pz5

    model = gp.Model("assignment")
    model.Params.OutputFlag = 0

    x = {}
    for p in range(6):
        for c in range(6):
            x[p, c] = model.addVar(vtype=GRB.BINARY, name=f"x_{p}_{c}")

    model.update()

    for p in range(6):
        model.addConstr(gp.quicksum(x[p, c] for c in range(6)) <= 1)

    for c in range(6):
        model.addConstr(gp.quicksum(x[p, c] for p in range(6)) <= 1)

    for p in range(6):
        for c in range(6):
            model.addConstr(x[p, c] <= pref[p][c])

    model.setObjective(
        gp.quicksum(assignment_value * x[p, c] for p in range(6) for c in range(6)),
        GRB.MAXIMIZE,
    )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    else:
        return {"objective": None, "status": "failed"}