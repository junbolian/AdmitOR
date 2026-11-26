import gurobipy as gp
from gurobipy import GRB
from itertools import combinations

def solve(params):
    cities = ['E', 'F', 'G', 'H', 'I']
    n = len(cities)
    idx = {c: i for i, c in enumerate(cities)}

    # Build symmetric cost matrix from params
    cost = {}
    for i, c1 in enumerate(cities):
        for j, c2 in enumerate(cities):
            if i == j:
                cost[i, j] = 0
            elif i < j:
                key = f"cost_{c1}_{c2}"
                cost[i, j] = params[key]
                cost[j, i] = params[key]

    model = gp.Model("TSP")
    model.setParam("OutputFlag", 0)

    # Binary variable x[i,j] = 1 if edge (i,j) is used
    x = model.addVars(n, n, vtype=GRB.BINARY, name="x")

    # No self-loops
    for i in range(n):
        model.addConstr(x[i, i] == 0)

    # Objective: minimize total travel cost
    model.setObjective(
        gp.quicksum(cost[i, j] * x[i, j] for i in range(n) for j in range(n) if i != j),
        GRB.MINIMIZE
    )

    # Each city is left exactly once
    for i in range(n):
        model.addConstr(gp.quicksum(x[i, j] for j in range(n) if j != i) == 1)

    # Each city is entered exactly once
    for j in range(n):
        model.addConstr(gp.quicksum(x[i, j] for i in range(n) if i != j) == 1)

    # Subtour elimination via MTZ formulation
    u = model.addVars(n, vtype=GRB.CONTINUOUS, name="u")
    for i in range(1, n):
        model.addConstr(u[i] >= 1)
        model.addConstr(u[i] <= n - 1)
    for i in range(1, n):
        for j in range(1, n):
            if i != j:
                model.addConstr(u[i] - u[j] + n * x[i, j] <= n - 1)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}