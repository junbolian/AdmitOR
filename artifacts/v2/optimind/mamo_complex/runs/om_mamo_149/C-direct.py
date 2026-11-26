import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n = 4
    cities = list(range(1, n + 1))

    # Build cost matrix from params
    cost = {}
    for i in cities:
        for j in cities:
            if i != j:
                cost[i, j] = params[f"cost_{i}_{j}"]

    model = gp.Model("TSP_4cities")
    model.setParam("OutputFlag", 0)

    # Binary decision variables: x[i,j] = 1 if travel from city i to city j
    x = model.addVars(cities, cities, vtype=GRB.BINARY, name="x")

    # No self-loops
    for i in cities:
        model.addConstr(x[i, i] == 0, name=f"no_self_loop_{i}")

    # Objective: minimize total travel cost
    model.setObjective(
        gp.quicksum(cost[i, j] * x[i, j] for i in cities for j in cities if i != j),
        GRB.MINIMIZE
    )

    # Each city is departed exactly once
    for i in cities:
        model.addConstr(
            gp.quicksum(x[i, j] for j in cities if j != i) == 1,
            name=f"depart_{i}"
        )

    # Each city is arrived at exactly once
    for j in cities:
        model.addConstr(
            gp.quicksum(x[i, j] for i in cities if i != j) == 1,
            name=f"arrive_{j}"
        )

    # Subtour elimination via MTZ formulation
    # u[i] is the position of city i in the tour (only for non-depot cities)
    # Using city 1 as the depot reference
    u = model.addVars(cities, vtype=GRB.CONTINUOUS, lb=1, ub=n, name="u")

    for i in cities:
        for j in cities:
            if i != j and i != 1 and j != 1:
                model.addConstr(
                    u[i] - u[j] + n * x[i, j] <= n - 1,
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