import gurobipy as gp
from gurobipy import GRB


def solve(params):
    cost = params["cost"]
    n = len(cost)

    model = gp.Model("assignment")
    model.Params.OutputFlag = 0

    x = {}
    for i in range(n):
        for j in range(n):
            x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    for i in range(n):
        model.addConstr(gp.quicksum(x[i, j] for j in range(n)) == 1, name=f"driver_{i}")

    for j in range(n):
        model.addConstr(gp.quicksum(x[i, j] for i in range(n)) == 1, name=f"route_{j}")

    model.setObjective(
        gp.quicksum(cost[i][j] * x[i, j] for i in range(n) for j in range(n)),
        GRB.MINIMIZE,
    )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    else:
        return {"objective": None, "status": "infeasible"}