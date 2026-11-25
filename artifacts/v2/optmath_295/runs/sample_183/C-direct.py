import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n = 8
    cities = list(range(n))

    # Build distance matrix from params
    dist = {}
    for i in cities:
        for j in cities:
            if i != j:
                dist[i, j] = params[f"dist_{i}_{j}"]

    model = gp.Model("tsp")
    model.setParam("OutputFlag", 0)

    # Binary decision variables: x[i,j] = 1 if travel from i to j
    x = model.addVars(
        [(i, j) for i in cities for j in cities if i != j],
        vtype=GRB.BINARY,
        name="x"
    )

    # Continuous position variables for MTZ subtour elimination
    # u[i] is the position of city i in the tour (1..n-1 for non-depot cities)
    u = model.addVars(cities, lb=0, ub=n - 1, vtype=GRB.CONTINUOUS, name="u")

    # Objective: minimize total distance
    model.setObjective(
        gp.quicksum(dist[i, j] * x[i, j] for i in cities for j in cities if i != j),
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

    # MTZ subtour elimination constraints
    # Fix depot position
    model.addConstr(u[0] == 0, name="depot_pos")

    for i in cities:
        if i == 0:
            continue
        model.addConstr(u[i] >= 1, name=f"pos_lb_{i}")
        model.addConstr(u[i] <= n - 1, name=f"pos_ub_{i}")

    for i in cities:
        for j in cities:
            if i != j and i != 0 and j != 0:
                model.addConstr(
                    u[i] - u[j] + (n - 1) * x[i, j] <= n - 2,
                    name=f"mtz_{i}_{j}"
                )
            elif i != 0 and j != 0 and j == 0:
                pass  # no constraint needed for arcs into depot via MTZ
            elif i != 0 and j == 0:
                pass

    # Additional MTZ constraints for arcs from non-depot to non-depot
    # Already handled above; also handle depot outgoing
    for j in cities:
        if j != 0:
            model.addConstr(
                u[j] >= 1 - (n - 1) * (1 - x[0, j]),
                name=f"mtz_depot_{j}"
            )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}