import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n = 4
    cities = list(range(1, n + 1))

    dist = {}
    for i in cities:
        for j in cities:
            if i != j:
                dist[i, j] = params[f"distance_{i}{j}"]

    model = gp.Model("TSP")
    model.setParam("OutputFlag", 0)

    # x[i,j] = 1 if salesman travels from city i to city j
    x = model.addVars(cities, cities, vtype=GRB.BINARY, name="x")

    # u[i] = position of city i in the tour (MTZ subtour elimination)
    u = model.addVars(cities, vtype=GRB.CONTINUOUS, name="u")

    # No self-loops
    for i in cities:
        model.addConstr(x[i, i] == 0)

    # Each city is departed exactly once
    for i in cities:
        model.addConstr(gp.quicksum(x[i, j] for j in cities if j != i) == 1)

    # Each city is entered exactly once
    for j in cities:
        model.addConstr(gp.quicksum(x[i, j] for i in cities if i != j) == 1)

    # MTZ subtour elimination constraints (for non-depot cities)
    for i in cities:
        if i != 1:
            model.addConstr(u[i] >= 1)
            model.addConstr(u[i] <= n - 1)

    for i in cities:
        for j in cities:
            if i != j and i != 1 and j != 1:
                model.addConstr(u[i] - u[j] + n * x[i, j] <= n - 1)

    # Objective: minimize total distance
    model.setObjective(
        gp.quicksum(dist[i, j] * x[i, j] for i in cities for j in cities if i != j),
        GRB.MINIMIZE
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}