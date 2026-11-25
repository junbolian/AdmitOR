import gurobipy as gp
from gurobipy import GRB


def solve(params):
    cost_matrix = params["cost_matrix"]
    n = len(cost_matrix)
    if n == 0 or any(len(row) != n for row in cost_matrix):
        return {"objective": None, "status": "invalid cost_matrix dimensions"}

    model = gp.Model("assignment")
    model.Params.OutputFlag = 0

    x = {}
    for i in range(n):
        for j in range(n):
            x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")
    model.update()

    model.setObjective(
        gp.quicksum(cost_matrix[i][j] * x[i, j] for i in range(n) for j in range(n)),
        GRB.MINIMIZE,
    )

    for i in range(n):
        model.addConstr(gp.quicksum(x[i, j] for j in range(n)) == 1, name=f"staff_{i}")
    for j in range(n):
        model.addConstr(gp.quicksum(x[i, j] for i in range(n)) == 1, name=f"zone_{j}")

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    return {"objective": None, "status": f"status_{model.status}"}