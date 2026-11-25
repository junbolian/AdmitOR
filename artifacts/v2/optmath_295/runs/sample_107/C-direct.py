import gurobipy as gp
from gurobipy import GRB


def solve(params):
    cities = [0, 1, 2, 3]
    n = len(cities)

    cost = {}
    for i in cities:
        for j in cities:
            if i != j:
                cost[(i, j)] = params[f"cost_{i}_{j}"]

    model = gp.Model("delivery_tsp")
    model.Params.OutputFlag = 0

    x = {}
    for i in cities:
        for j in cities:
            if i != j:
                x[(i, j)] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    u = {}
    for i in cities:
        u[i] = model.addVar(lb=0, ub=n - 1, vtype=GRB.INTEGER, name=f"u_{i}")

    model.update()

    model.addConstr(u[0] == 0, name="fix_pos_0")

    for j in cities:
        model.addConstr(
            gp.quicksum(x[(i, j)] for i in cities if i != j) == 1,
            name=f"in_degree_{j}",
        )

    for i in cities:
        model.addConstr(
            gp.quicksum(x[(i, j)] for j in cities if j != i) == 1,
            name=f"out_degree_{i}",
        )

    M = n - 1
    for i in range(1, n):
        for j in range(1, n):
            if i != j:
                model.addConstr(
                    u[j] >= u[i] + 1 - M * (1 - x[(i, j)]),
                    name=f"mtz_{i}_{j}",
                )

    model.setObjective(
        gp.quicksum(cost[(i, j)] * x[(i, j)] for i in cities for j in cities if i != j),
        GRB.MINIMIZE,
    )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    else:
        return {"objective": None, "status": "infeasible"}