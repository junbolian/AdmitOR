import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n = 7
    cities = list(range(n))

    # Build cost dict from params
    cost = {}
    for i in cities:
        for j in cities:
            if i != j:
                cost[i, j] = params[f"cost_{i}_{j}"]

    model = gp.Model("TSP")
    model.setParam("OutputFlag", 0)

    # Binary decision variables: x[i,j] = 1 if route i->j is taken
    x = model.addVars(
        [(i, j) for i in cities for j in cities if i != j],
        vtype=GRB.BINARY,
        name="x"
    )

    # MTZ auxiliary variables: position of each city in the tour
    # City 0 is fixed at position 0; others in [1, n-1]
    u = model.addVars(cities, lb=0.0, ub=n - 1, vtype=GRB.CONTINUOUS, name="u")

    # Objective: minimize total travel cost
    model.setObjective(
        gp.quicksum(cost[i, j] * x[i, j] for i in cities for j in cities if i != j),
        GRB.MINIMIZE
    )

    # Each city is arrived at exactly once
    for j in cities:
        model.addConstr(
            gp.quicksum(x[i, j] for i in cities if i != j) == 1,
            name=f"arrive_{j}"
        )

    # Each city is departed from exactly once
    for i in cities:
        model.addConstr(
            gp.quicksum(x[i, j] for j in cities if i != j) == 1,
            name=f"depart_{i}"
        )

    # Fix position of starting city
    model.addConstr(u[0] == 0, name="u_start")

    # MTZ subtour elimination constraints for non-depot cities
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

    # Position bounds for non-depot cities: between 1 and n-1
    for i in cities:
        if i != 0:
            model.addConstr(u[i] >= 1, name=f"u_lb_{i}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}