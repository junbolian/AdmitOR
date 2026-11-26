import gurobipy as gp
from gurobipy import GRB
from itertools import combinations

def solve(params):
    n = 6
    cities = list(range(1, n + 1))

    # Build symmetric cost dict from params
    cost = {}
    for i in cities:
        for j in cities:
            if i == j:
                cost[i, j] = 0
            elif i < j:
                cost[i, j] = params[f"cost_{i}_{j}"]
                cost[j, i] = params[f"cost_{i}_{j}"]

    model = gp.Model("TSP")
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i,j] = 1 if we travel from i to j
    x = {}
    for i in cities:
        for j in cities:
            if i != j:
                x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    # Objective: minimize total travel cost
    model.setObjective(
        gp.quicksum(cost[i, j] * x[i, j] for i in cities for j in cities if i != j),
        GRB.MINIMIZE
    )

    # Each city must be left exactly once
    for i in cities:
        model.addConstr(
            gp.quicksum(x[i, j] for j in cities if j != i) == 1,
            name=f"leave_{i}"
        )

    # Each city must be entered exactly once
    for j in cities:
        model.addConstr(
            gp.quicksum(x[i, j] for i in cities if i != j) == 1,
            name=f"enter_{j}"
        )

    # Subtour elimination via MTZ formulation
    # u[i] is the position of city i in the tour (for i != 1)
    u = {}
    for i in cities:
        if i != 1:
            u[i] = model.addVar(lb=1, ub=n - 1, vtype=GRB.CONTINUOUS, name=f"u_{i}")

    for i in cities:
        for j in cities:
            if i != j and i != 1 and j != 1:
                model.addConstr(
                    u[i] - u[j] + (n - 1) * x[i, j] <= n - 2,
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