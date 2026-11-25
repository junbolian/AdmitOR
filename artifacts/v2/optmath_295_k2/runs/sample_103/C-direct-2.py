import gurobipy as gp
from gurobipy import GRB


def solve(params):
    cost = params["cost"]

    num_peaks = 4
    num_amino = 5

    model = gp.Model("nmr_assignment")

    x = {}
    for i in range(num_peaks):
        for j in range(num_amino):
            x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    model.setObjective(
        gp.quicksum(
            cost[i][j] * x[i, j]
            for i in range(num_peaks)
            for j in range(num_amino)
        ),
        GRB.MINIMIZE,
    )

    for i in range(num_peaks):
        model.addConstr(gp.quicksum(x[i, j] for j in range(num_amino)) <= 1)

    for j in range(num_amino):
        model.addConstr(gp.quicksum(x[i, j] for i in range(num_peaks)) <= 1)

    model.addConstr(
        gp.quicksum(
            x[i, j] for i in range(num_peaks) for j in range(num_amino)
        ) == 2
    )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    else:
        return {"objective": None, "status": "failed"}