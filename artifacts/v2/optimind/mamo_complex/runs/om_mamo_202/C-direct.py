import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n = 6
    cities = list(range(1, n + 1))

    # Build cost dict from params
    cost = {}
    for i in cities:
        for j in cities:
            if i != j:
                cost[i, j] = params[f"c{i}{j}"]

    model = gp.Model("TSP")
    model.setParam("OutputFlag", 0)

    # x[i,j] = 1 if travel from city i to city j
    x = model.addVars(cities, cities, vtype=GRB.BINARY, name="x")

    # u[i] = subtour elimination position variable (MTZ), for i in 2..n
    u = model.addVars(cities, vtype=GRB.CONTINUOUS, name="u")

    # No self-loops
    for i in cities:
        model.addConstr(x[i, i] == 0)

    # Objective
    model.setObjective(
        gp.quicksum(cost[i, j] * x[i, j] for i in cities for j in cities if i != j),
        GRB.MINIMIZE
    )

    # Each city is left exactly once
    for i in cities:
        model.addConstr(gp.quicksum(x[i, j] for j in cities if j != i) == 1)

    # Each city is entered exactly once
    for j in cities:
        model.addConstr(gp.quicksum(x[i, j] for i in cities if i != j) == 1)

    # MTZ subtour elimination
    for i in cities:
        model.addConstr(u[i] >= 1)
        model.addConstr(u[i] <= n)

    for i in cities:
        for j in cities:
            if i != j and j != 1:
                model.addConstr(u[i] - u[j] + n * x[i, j] <= n - 1)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}