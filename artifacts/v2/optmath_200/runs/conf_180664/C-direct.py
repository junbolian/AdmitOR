import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n = 5  # number of cities
    cities = list(range(n))

    # Build distance matrix from params
    dist = {}
    for i in cities:
        for j in cities:
            if i != j:
                dist[i, j] = params[f"dist_{i}_{j}"]

    u_min = params["u_min"]
    u_max = params["u_max"]

    model = gp.Model("TSP")
    model.setParam("OutputFlag", 0)

    # Binary decision variables: x[i,j] = 1 if travel from i to j
    x = model.addVars(cities, cities, vtype=GRB.BINARY, name="x")
    # Remove self-loops
    for i in cities:
        model.addConstr(x[i, i] == 0)

    # Position variables for MTZ subtour elimination (cities 1..4)
    u = model.addVars(cities[1:], lb=u_min, ub=u_max, vtype=GRB.CONTINUOUS, name="u")

    # Objective: minimize total distance
    model.setObjective(
        gp.quicksum(dist[i, j] * x[i, j] for i in cities for j in cities if i != j),
        GRB.MINIMIZE
    )

    # Each city must be entered exactly once
    for j in cities:
        model.addConstr(gp.quicksum(x[i, j] for i in cities if i != j) == 1, name=f"enter_{j}")

    # Each city must be left exactly once
    for i in cities:
        model.addConstr(gp.quicksum(x[i, j] for j in cities if i != j) == 1, name=f"leave_{i}")

    # MTZ subtour elimination constraints for cities 1..4
    for i in cities[1:]:
        for j in cities[1:]:
            if i != j:
                model.addConstr(
                    u[i] - u[j] + (u_max - u_min + 1) * x[i, j] <= u_max - u_min,
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