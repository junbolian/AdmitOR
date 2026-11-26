import gurobipy as gp
from gurobipy import GRB
from itertools import combinations

def solve(params):
    cities = ['E', 'F', 'G', 'H', 'I']
    n = len(cities)
    idx = {c: i for i, c in enumerate(cities)}

    cost = {}
    for i in cities:
        for j in cities:
            if i != j:
                key = f"cost_{i}{j}"
                cost[(i, j)] = params[key]

    model = gp.Model("TSP")
    model.setParam("OutputFlag", 0)

    x = {}
    for i in cities:
        for j in cities:
            if i != j:
                x[(i, j)] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}{j}")

    model.setObjective(
        gp.quicksum(cost[(i, j)] * x[(i, j)] for i in cities for j in cities if i != j),
        GRB.MINIMIZE
    )

    # Each city is left exactly once
    for i in cities:
        model.addConstr(gp.quicksum(x[(i, j)] for j in cities if j != i) == 1, name=f"leave_{i}")

    # Each city is entered exactly once
    for j in cities:
        model.addConstr(gp.quicksum(x[(i, j)] for i in cities if i != j) == 1, name=f"enter_{j}")

    # Subtour elimination (MTZ)
    u = {}
    for i in cities:
        u[i] = model.addVar(lb=0, ub=n - 1, vtype=GRB.CONTINUOUS, name=f"u_{i}")

    # Fix one city's u to break symmetry
    model.addConstr(u['E'] == 0, name="u_fix")

    for i in cities:
        for j in cities:
            if i != j and j != 'E':
                model.addConstr(
                    u[i] - u[j] + n * x[(i, j)] <= n - 1,
                    name=f"mtz_{i}_{j}"
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