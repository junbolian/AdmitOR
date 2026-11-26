import gurobipy as gp
from gurobipy import GRB
from itertools import combinations

def solve(params):
    cost_matrix = params["cost_matrix"]
    n = 5
    cities = list(range(1, n + 1))

    model = gp.Model("TSP")
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i,j] = 1 if travel from city i to city j
    x = {}
    for i in cities:
        for j in cities:
            if i != j:
                x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    # Objective: minimize total travel cost
    model.setObjective(
        gp.quicksum(cost_matrix[i - 1][j - 1] * x[i, j] for i in cities for j in cities if i != j),
        GRB.MINIMIZE
    )

    # Each city must be left exactly once
    for i in cities:
        model.addConstr(gp.quicksum(x[i, j] for j in cities if j != i) == 1, name=f"leave_{i}")

    # Each city must be entered exactly once
    for j in cities:
        model.addConstr(gp.quicksum(x[i, j] for i in cities if i != j) == 1, name=f"enter_{j}")

    # Subtour elimination using MTZ formulation
    u = {}
    for i in cities:
        u[i] = model.addVar(lb=1, ub=n, vtype=GRB.CONTINUOUS, name=f"u_{i}")

    for i in cities:
        for j in cities:
            if i != j and j != 1:
                model.addConstr(
                    u[i] - u[j] + n * x[i, j] <= n - 1,
                    name=f"mtz_{i}_{j}"
                )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}