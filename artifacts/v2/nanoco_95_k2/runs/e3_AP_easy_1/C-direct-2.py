import gurobipy as gp
from gurobipy import GRB


def solve(params):
    cost_matrix = params["cost_matrix"]
    n = len(cost_matrix)
    m = len(cost_matrix[0])

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(n, m, vtype=GRB.BINARY, name="x")

    model.setObjective(
        gp.quicksum(cost_matrix[i][j] * x[i, j] for i in range(n) for j in range(m)),
        GRB.MINIMIZE
    )

    for i in range(n):
        model.addConstr(gp.quicksum(x[i, j] for j in range(m)) == 1, name=f"vm_{i}")

    for j in range(m):
        model.addConstr(gp.quicksum(x[i, j] for i in range(n)) == 1, name=f"node_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}