import gurobipy as gp
from gurobipy import GRB


def solve(params):
    cost_matrix = params["cost_matrix"]
    n = len(cost_matrix)  # 6 technicians, 6 jobs

    model = gp.Model("dispatch")
    model.Params.OutputFlag = 0

    x = {}
    for i in range(n):
        for j in range(n):
            x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    model.modelSense = GRB.MINIMIZE
    model.setObjective(
        gp.quicksum(cost_matrix[i][j] * x[i, j] for i in range(n) for j in range(n))
    )

    for i in range(n):
        model.addConstr(gp.quicksum(x[i, j] for j in range(n)) == 1, name=f"tech_{i}")

    for j in range(n):
        model.addConstr(gp.quicksum(x[i, j] for i in range(n)) == 1, name=f"job_{j}")

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}

    return {"objective": None, "status": f"status_{model.status}"}