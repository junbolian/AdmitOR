import gurobipy as gp
from gurobipy import GRB


def solve(params):
    tt = params["travel_time_matrix"]
    n = 8
    nodes = list(range(n))

    model = gp.Model("vaccination_tsp")
    model.setParam("OutputFlag", 0)

    x = {}
    for i in nodes:
        for j in nodes:
            if i != j:
                x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    u = {}
    for i in nodes:
        if i != 0:
            u[i] = model.addVar(vtype=GRB.CONTINUOUS, lb=0.0, ub=n - 1, name=f"u_{i}")

    model.update()

    model.setObjective(
        gp.quicksum(tt[i][j] * x[i, j] for i in nodes for j in nodes if i != j),
        GRB.MINIMIZE,
    )

    for j in nodes:
        model.addConstr(
            gp.quicksum(x[i, j] for i in nodes if i != j) == 1, name=f"in_{j}"
        )

    for i in nodes:
        model.addConstr(
            gp.quicksum(x[i, j] for j in nodes if i != j) == 1, name=f"out_{i}"
        )

    for i in nodes:
        if i == 0:
            continue
        for j in nodes:
            if j == 0 or i == j:
                continue
            model.addConstr(
                u[i] - u[j] + n * x[i, j] <= n - 1, name=f"mtz_{i}_{j}"
            )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.objVal), "status": "optimal"}

    return {"objective": None, "status": "failed"}