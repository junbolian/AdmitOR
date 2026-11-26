import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n = 5
    cities = list(range(1, n + 1))

    # Build cost dictionary from params
    cost = {}
    for i in cities:
        for j in cities:
            if i != j:
                cost[i, j] = params[f"cost_{i}_{j}"]

    model = gp.Model("TSP")
    model.Params.OutputFlag = 0

    # Decision variables: x[i,j] = 1 if travel from i to j
    x = model.addVars(cities, cities, vtype=GRB.BINARY, name="x")

    # MTZ subtour elimination variables
    u = model.addVars(cities, vtype=GRB.CONTINUOUS, name="u")

    # No self-loops
    for i in cities:
        model.addConstr(x[i, i] == 0)

    # Objective: minimize total travel cost
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

    # MTZ subtour elimination constraints
    # Fix u[1] = 1 and for others: 2 <= u[i] <= n
    model.addConstr(u[1] == 1)
    for i in cities[1:]:
        model.addConstr(u[i] >= 2)
        model.addConstr(u[i] <= n)

    for i in cities[1:]:
        for j in cities[1:]:
            if i != j:
                model.addConstr(u[i] - u[j] + n * x[i, j] <= n - 1)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}