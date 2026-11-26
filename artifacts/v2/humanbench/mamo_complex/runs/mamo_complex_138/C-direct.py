import gurobipy as gp
from gurobipy import Model, GRB, quicksum


def solve(params):
    cost = params["cost_matrix"]
    n = len(cost)
    if n < 3:
        return {"objective": None, "status": "trivial"}

    model = Model("tsp")
    x = model.addVars(n, n, vtype=GRB.BINARY, name="x")
    u = model.addVars(n, vtype=GRB.CONTINUOUS, lb=0, ub=n - 1, name="u")

    model.setObjective(
        quicksum(cost[i][j] * x[i, j] for i in range(n) for j in range(n) if i != j),
        GRB.MINIMIZE,
    )

    for i in range(n):
        model.addConstr(quicksum(x[i, j] for j in range(n) if j != i) == 1)
        model.addConstr(quicksum(x[j, i] for j in range(n) if j != i) == 1)

    # MTZ subtour elimination (fix u[0] = 0)
    for i in range(1, n):
        for j in range(1, n):
            if i != j:
                model.addConstr(u[i] - u[j] + (n - 1) * x[i, j] <= n - 2)

    model.Params.LogToConsole = 0
    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    return {"objective": None, "status": "no_solution"}