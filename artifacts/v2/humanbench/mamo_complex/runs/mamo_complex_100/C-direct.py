import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cities = ['A', 'B', 'C', 'D']
    n = len(cities)

    cost = {}
    for i in cities:
        for j in cities:
            if i != j:
                key = f"cost_{i}_{j}"
                cost[(i, j)] = params[key]

    model = gp.Model("TSP_4cities")
    model.setParam("OutputFlag", 0)

    # x[i,j] = 1 if we travel from city i to city j
    x = model.addVars(
        [(i, j) for i in cities for j in cities if i != j],
        vtype=GRB.BINARY,
        name="x"
    )

    # u[i] = position of city i in tour (MTZ subtour elimination), u in [1, n-1] for non-depot
    # Fix A as depot (position 0); u for B, C, D in [1, n-1]
    non_depot = ['B', 'C', 'D']
    u = model.addVars(non_depot, vtype=GRB.CONTINUOUS, name="u", lb=1, ub=n - 1)

    # Objective: minimize total travel cost
    model.setObjective(
        gp.quicksum(cost[(i, j)] * x[(i, j)] for i in cities for j in cities if i != j),
        GRB.MINIMIZE
    )

    # Each city is departed exactly once
    for i in cities:
        model.addConstr(
            gp.quicksum(x[(i, j)] for j in cities if j != i) == 1,
            name=f"depart_{i}"
        )

    # Each city is arrived at exactly once
    for j in cities:
        model.addConstr(
            gp.quicksum(x[(i, j)] for i in cities if i != j) == 1,
            name=f"arrive_{j}"
        )

    # MTZ subtour elimination constraints
    for i in non_depot:
        for j in non_depot:
            if i != j:
                model.addConstr(
                    u[i] - u[j] + (n - 1) * x[(i, j)] <= n - 2,
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