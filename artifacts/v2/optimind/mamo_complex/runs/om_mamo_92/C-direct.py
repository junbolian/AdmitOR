import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cities = ['A', 'B', 'C', 'D']
    n = len(cities)

    cost = {}
    for i in cities:
        for j in cities:
            if i != j:
                key = f"cost_{i}_{j}"
                cost[i, j] = params[key]

    model = gp.Model("TSP")
    model.setParam("OutputFlag", 0)

    # Binary variable x[i,j] = 1 if travel from i to j
    x = model.addVars(cities, cities, vtype=GRB.BINARY, name="x")

    # Subtour elimination variables (MTZ formulation)
    u = model.addVars(cities, vtype=GRB.CONTINUOUS, name="u")

    # No self-loops
    for i in cities:
        model.addConstr(x[i, i] == 0)

    # Each city is left exactly once
    for i in cities:
        model.addConstr(gp.quicksum(x[i, j] for j in cities if j != i) == 1)

    # Each city is entered exactly once
    for j in cities:
        model.addConstr(gp.quicksum(x[i, j] for i in cities if i != j) == 1)

    # MTZ subtour elimination
    # Fix u for first city to break symmetry
    model.addConstr(u['A'] == 1)
    non_start = [c for c in cities if c != 'A']
    for i in non_start:
        model.addConstr(u[i] >= 2)
        model.addConstr(u[i] <= n)
    for i in non_start:
        for j in non_start:
            if i != j:
                model.addConstr(u[i] - u[j] + n * x[i, j] <= n - 1)

    # Objective
    model.setObjective(
        gp.quicksum(cost[i, j] * x[i, j] for i in cities for j in cities if i != j),
        GRB.MINIMIZE
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}