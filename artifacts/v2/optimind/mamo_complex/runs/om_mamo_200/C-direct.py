import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost_matrix = params["cost_matrix"]
    n = 5
    cities = list(range(n))

    model = gp.Model("TSP")
    model.setParam("OutputFlag", 0)

    # x[i,j] = 1 if travel from city i to city j
    x = {}
    for i in cities:
        for j in cities:
            if i != j:
                x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    # u[i] = position of city i in tour (MTZ subtour elimination)
    u = {}
    for i in cities:
        u[i] = model.addVar(lb=0, ub=n - 1, vtype=GRB.CONTINUOUS, name=f"u_{i}")

    # Objective
    model.setObjective(
        gp.quicksum(cost_matrix[i][j] * x[i, j] for i in cities for j in cities if i != j),
        GRB.MINIMIZE
    )

    # Each city is left exactly once
    for i in cities:
        model.addConstr(gp.quicksum(x[i, j] for j in cities if j != i) == 1, name=f"leave_{i}")

    # Each city is entered exactly once
    for j in cities:
        model.addConstr(gp.quicksum(x[i, j] for i in cities if i != j) == 1, name=f"enter_{j}")

    # MTZ subtour elimination constraints
    for i in cities[1:]:
        for j in cities[1:]:
            if i != j:
                model.addConstr(u[i] - u[j] + n * x[i, j] <= n - 1, name=f"mtz_{i}_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}