import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cities = ['A', 'B', 'C', 'D']
    n = len(cities)
    idx = {c: i for i, c in enumerate(cities)}

    cost = {}
    for c1 in cities:
        for c2 in cities:
            if c1 != c2:
                key = f"cost_{c1}{c2}"
                cost[(c1, c2)] = params[key]

    model = gp.Model("TSP")
    model.setParam("OutputFlag", 0)

    # Binary variable x[i,j] = 1 if travel from city i to city j
    x = {}
    for c1 in cities:
        for c2 in cities:
            if c1 != c2:
                x[(c1, c2)] = model.addVar(vtype=GRB.BINARY, name=f"x_{c1}{c2}")

    # MTZ subtour elimination variables
    u = {}
    for c in cities:
        u[c] = model.addVar(lb=0, ub=n - 1, vtype=GRB.CONTINUOUS, name=f"u_{c}")

    # Objective: minimize total travel cost
    model.setObjective(
        gp.quicksum(cost[(c1, c2)] * x[(c1, c2)] for c1 in cities for c2 in cities if c1 != c2),
        GRB.MINIMIZE
    )

    # Each city is departed exactly once
    for c1 in cities:
        model.addConstr(
            gp.quicksum(x[(c1, c2)] for c2 in cities if c1 != c2) == 1,
            name=f"depart_{c1}"
        )

    # Each city is arrived at exactly once
    for c2 in cities:
        model.addConstr(
            gp.quicksum(x[(c1, c2)] for c1 in cities if c1 != c2) == 1,
            name=f"arrive_{c2}"
        )

    # MTZ subtour elimination constraints
    # Fix starting city to have u = 0 to break symmetry (optional but helps)
    # For all i != j (both not the first city), u[i] - u[j] + n*x[i,j] <= n-1
    start = 'A'
    for c1 in cities:
        for c2 in cities:
            if c1 != c2 and c2 != start:
                model.addConstr(
                    u[c1] - u[c2] + n * x[(c1, c2)] <= n - 1,
                    name=f"mtz_{c1}_{c2}"
                )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}