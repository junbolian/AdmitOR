import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost_matrix = params["cost_matrix"]
    num_cities = params["num_cities"]

    n = num_cities
    cities = list(range(n))

    model = gp.Model("TSP")
    model.setParam("OutputFlag", 0)

    # x[i,j] = 1 if courier travels from city i to city j
    x = {}
    for i in cities:
        for j in cities:
            if i != j:
                x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    # u[i] = position of city i in the tour (MTZ formulation), for i != 0
    u = {}
    for i in cities:
        if i != 0:
            u[i] = model.addVar(lb=1, ub=n - 1, vtype=GRB.CONTINUOUS, name=f"u_{i}")

    # Objective: minimize total travel cost
    model.setObjective(
        gp.quicksum(cost_matrix[i][j] * x[i, j] for i in cities for j in cities if i != j),
        GRB.MINIMIZE
    )

    # Each city is departed exactly once
    for i in cities:
        model.addConstr(gp.quicksum(x[i, j] for j in cities if j != i) == 1, name=f"depart_{i}")

    # Each city is arrived at exactly once
    for j in cities:
        model.addConstr(gp.quicksum(x[i, j] for i in cities if i != j) == 1, name=f"arrive_{j}")

    # MTZ subtour elimination constraints
    for i in cities:
        if i == 0:
            continue
        for j in cities:
            if j == 0 or i == j:
                continue
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