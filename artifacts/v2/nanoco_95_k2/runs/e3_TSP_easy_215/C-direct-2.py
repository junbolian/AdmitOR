import gurobipy as gp
from gurobipy import GRB

def solve(params):
    distance_matrix = params["distance_matrix"]
    n = len(distance_matrix)

    model = gp.Model("cold_chain_tsp")
    model.Params.OutputFlag = 0

    x = {}
    for i in range(n):
        for j in range(n):
            if i != j:
                x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    u = {}
    for i in range(1, n):
        u[i] = model.addVar(vtype=GRB.CONTINUOUS, lb=1.0, ub=float(n - 1), name=f"u_{i}")

    model.setObjective(
        gp.quicksum(distance_matrix[i][j] * x[i, j]
                     for i in range(n) for j in range(n) if i != j),
        GRB.MINIMIZE,
    )

    for j in range(n):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(n) if i != j) == 1,
            name=f"enter_{j}",
        )

    for i in range(n):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(n) if i != j) == 1,
            name=f"leave_{i}",
        )

    for i in range(1, n):
        for j in range(1, n):
            if i != j:
                model.addConstr(
                    u[i] - u[j] + n * x[i, j] <= n - 1,
                    name=f"mtz_{i}_{j}",
                )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    else:
        return {"objective": None, "status": "not_optimal"}