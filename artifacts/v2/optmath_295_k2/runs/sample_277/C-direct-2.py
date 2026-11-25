import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n = 6
    cities = list(range(n))

    # Build distance matrix from params
    dist = {}
    for i in cities:
        for j in cities:
            if i != j:
                dist[i, j] = params[f"dist_{i}_{j}"]

    model = gp.Model("TSP")
    model.setParam("OutputFlag", 0)

    # Binary route selection variables x[i,j] = 1 if we travel from i to j
    x = model.addVars(cities, cities, vtype=GRB.BINARY, name="x")
    for i in cities:
        model.addConstr(x[i, i] == 0)

    # Position variables u[i] for MTZ subtour elimination
    u = model.addVars(cities, vtype=GRB.CONTINUOUS, lb=0, ub=n - 1, name="u")

    # Objective: minimize total distance
    model.setObjective(
        gp.quicksum(dist[i, j] * x[i, j] for i in cities for j in cities if i != j),
        GRB.MINIMIZE
    )

    # Each city has exactly one outgoing route
    for i in cities:
        model.addConstr(gp.quicksum(x[i, j] for j in cities if j != i) == 1)

    # Each city has exactly one incoming route
    for j in cities:
        model.addConstr(gp.quicksum(x[i, j] for i in cities if i != j) == 1)

    # Fix City 0 at position 0
    model.addConstr(u[0] == 0)

    # MTZ subtour elimination constraints
    for i in cities:
        for j in cities:
            if i != j and j != 0:
                model.addConstr(u[j] >= u[i] + 1 - n * (1 - x[i, j]))

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}