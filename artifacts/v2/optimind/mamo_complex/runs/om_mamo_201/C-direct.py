import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cities = ['A', 'B', 'C', 'D', 'E']
    n = len(cities)
    idx = {c: i for i, c in enumerate(cities)}

    cost = {}
    for i in cities:
        for j in cities:
            if i != j:
                key = f"cost_{i}_{j}"
                cost[(i, j)] = params[key]

    model = gp.Model("TSP")
    model.setParam("OutputFlag", 0)

    x = model.addVars(cities, cities, vtype=GRB.BINARY, name="x")

    # No self-loops
    for c in cities:
        model.addConstr(x[c, c] == 0)

    # Each city is left exactly once
    for i in cities:
        model.addConstr(gp.quicksum(x[i, j] for j in cities if j != i) == 1)

    # Each city is entered exactly once
    for j in cities:
        model.addConstr(gp.quicksum(x[i, j] for i in cities if i != j) == 1)

    # MTZ subtour elimination
    u = model.addVars(cities, lb=0.0, ub=n - 1, vtype=GRB.CONTINUOUS, name="u")
    # Fix u for first city to break symmetry (optional but helps)
    model.addConstr(u['A'] == 0)
    for i in cities:
        for j in cities:
            if i != j and j != 'A':
                model.addConstr(u[i] - u[j] + n * x[i, j] <= n - 1)

    model.setObjective(
        gp.quicksum(cost[(i, j)] * x[i, j] for i in cities for j in cities if i != j),
        GRB.MINIMIZE
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}