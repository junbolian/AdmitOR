import gurobipy as gp
from gurobipy import GRB


def solve(params):
    n = params["n_cities"]
    d = params["distance_matrix"]

    cities = list(range(n))

    model = gp.Model("TSP")
    model.setParam("OutputFlag", 0)

    # x[i,j] = 1 if we travel from city i to city j
    x = model.addVars(cities, cities, vtype=GRB.BINARY, name="x")

    # u[i] = position of city i in the tour (MTZ subtour elimination)
    # u[0] is fixed as the starting city
    u = model.addVars(cities, vtype=GRB.CONTINUOUS, name="u")

    # Objective: minimize total distance
    model.setObjective(
        gp.quicksum(d[i][j] * x[i, j] for i in cities for j in cities if i != j),
        GRB.MINIMIZE
    )

    # Each city must be entered exactly once
    for j in cities:
        model.addConstr(
            gp.quicksum(x[i, j] for i in cities if i != j) == 1,
            name=f"enter_{j}"
        )

    # Each city must be left exactly once
    for i in cities:
        model.addConstr(
            gp.quicksum(x[i, j] for j in cities if i != j) == 1,
            name=f"leave_{i}"
        )

    # No self-loops
    for i in cities:
        model.addConstr(x[i, i] == 0, name=f"no_self_{i}")

    # MTZ subtour elimination constraints
    # u[0] = 0 (fix starting city position)
    model.addConstr(u[0] == 0, name="start_position")

    for i in cities[1:]:
        model.addConstr(u[i] >= 1, name=f"u_lb_{i}")
        model.addConstr(u[i] <= n - 1, name=f"u_ub_{i}")

    # MTZ linking constraints: if x[i,j]=1 then u[j] >= u[i] + 1
    for i in cities[1:]:
        for j in cities[1:]:
            if i != j:
                model.addConstr(
                    u[j] >= u[i] + 1 - n * (1 - x[i, j]),
                    name=f"mtz_{i}_{j}"
                )

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}