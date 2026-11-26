import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cities = ['E', 'F', 'G', 'H', 'I']
    n = len(cities)
    idx = {c: i for i, c in enumerate(cities)}

    # Build cost matrix from params
    cost = {}
    for i in cities:
        for j in cities:
            if i != j:
                key = f"cost_{i}_{j}"
                cost[i, j] = params[key]

    model = gp.Model("TSP")
    model.setParam("OutputFlag", 0)

    # x[i,j] = 1 if we travel from city i to city j
    x = model.addVars(cities, cities, vtype=GRB.BINARY, name="x")

    # Subtour elimination variables (MTZ formulation)
    u = model.addVars(cities, vtype=GRB.CONTINUOUS, name="u")

    # No self-loops
    for c in cities:
        model.addConstr(x[c, c] == 0)

    # Objective
    model.setObjective(
        gp.quicksum(cost[i, j] * x[i, j] for i in cities for j in cities if i != j),
        GRB.MINIMIZE
    )

    # Each city is departed exactly once
    for i in cities:
        model.addConstr(gp.quicksum(x[i, j] for j in cities if j != i) == 1)

    # Each city is entered exactly once
    for j in cities:
        model.addConstr(gp.quicksum(x[i, j] for i in cities if i != j) == 1)

    # MTZ subtour elimination
    for i in cities:
        u[i].lb = 0
        u[i].ub = n - 1

    # Fix u for first city to break symmetry
    model.addConstr(u['E'] == 0)

    for i in cities:
        for j in cities:
            if i != j and j != 'E':
                model.addConstr(u[i] - u[j] + n * x[i, j] <= n - 1)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}