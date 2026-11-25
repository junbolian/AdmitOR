import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n = 5
    cities = list(range(n))

    cost = {}
    for i in cities:
        for j in cities:
            if i != j:
                key = f"cost_{i}_{j}"
                cost[i, j] = params[key]

    model = gp.Model("tsp")
    model.setParam("OutputFlag", 0)

    x = model.addVars(cities, cities, vtype=GRB.BINARY, name="x")
    u = model.addVars(cities, vtype=GRB.CONTINUOUS, name="u")

    # No self-loops
    for i in cities:
        x[i, i].ub = 0

    # Objective
    model.setObjective(
        gp.quicksum(cost[i, j] * x[i, j] for i in cities for j in cities if i != j),
        GRB.MINIMIZE
    )

    # Each city entered exactly once
    for j in cities:
        model.addConstr(gp.quicksum(x[i, j] for i in cities if i != j) == 1, name=f"enter_{j}")

    # Each city departed exactly once
    for i in cities:
        model.addConstr(gp.quicksum(x[i, j] for j in cities if i != j) == 1, name=f"depart_{i}")

    # MTZ subtour elimination: u[i] - u[j] + n*x[i,j] <= n-1 for i,j != 0
    for i in cities:
        if i == 0:
            continue
        for j in cities:
            if j == 0 or i == j:
                continue
            model.addConstr(u[i] - u[j] + n * x[i, j] <= n - 1, name=f"mtz_{i}_{j}")

    # Position bounds for cities 1..4
    for i in range(1, n):
        u[i].lb = 1
        u[i].ub = n - 1

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}