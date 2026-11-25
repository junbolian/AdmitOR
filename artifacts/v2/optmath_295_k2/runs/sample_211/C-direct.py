import gurobipy as gp
from gurobipy import GRB


def solve(params):
    N = 5
    cities = list(range(N))

    # Read asymmetric travel costs from params
    cost = {}
    for i in cities:
        for j in cities:
            if i != j:
                cost[i, j] = params[f"cost_{i}_{j}"]

    model = gp.Model("tsp")

    # Binary arc variables: x[i,j] = 1 if route goes directly from city i to city j
    x = {}
    for i in cities:
        for j in cities:
            if i != j:
                x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    # Position variables (Miller-Tucker-Zemlin ordering), positions 0..N-1
    u = {}
    for i in cities:
        u[i] = model.addVar(lb=0, ub=N - 1, vtype=GRB.INTEGER, name=f"u_{i}")

    model.setObjective(
        gp.quicksum(cost[i, j] * x[i, j]
                    for i in cities for j in cities if i != j),
        GRB.MINIMIZE,
    )

    # Depart each city exactly once
    for i in cities:
        model.addConstr(
            gp.quicksum(x[i, j] for j in cities if i != j) == 1,
            name=f"depart_{i}",
        )

    # Arrive at each city exactly once
    for j in cities:
        model.addConstr(
            gp.quicksum(x[i, j] for i in cities if i != j) == 1,
            name=f"arrive_{j}",
        )

    # Fix depot position to 0 (use city 0 as the depot for MTZ)
    model.addConstr(u[0] == 0, name="pos_depot")

    # MTZ subtour-elimination constraints
    for i in cities:
        if i == 0:
            continue
        for j in cities:
            if j == 0 or j == i:
                continue
            model.addConstr(
                u[i] - u[j] + N * x[i, j] <= N - 1,
                name=f"mtz_{i}_{j}",
            )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    return {"objective": None, "status": "no optimal solution"}