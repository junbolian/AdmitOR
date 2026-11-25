import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost = params["cost"]
    n = len(cost)
    pos_city0 = params["position_city0"]
    pos_min = params["position_min_others"]
    pos_max = params["position_max_others"]

    model = gp.Model("tsp")
    model.Params.OutputFlag = 0

    # Binary route variables x[i, j] for i != j
    x = {}
    for i in range(n):
        for j in range(n):
            if i != j:
                x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    # Position variables u[i] for each city
    u = {}
    for i in range(n):
        u[i] = model.addVar(vtype=GRB.CONTINUOUS, name=f"u_{i}")

    model.update()

    # Fix position of city 0
    model.addConstr(u[0] == pos_city0, name="fix_city0")

    # Position bounds for cities 1..n-1
    for i in range(1, n):
        model.addConstr(u[i] >= pos_min, name=f"pos_min_{i}")
        model.addConstr(u[i] <= pos_max, name=f"pos_max_{i}")

    # Each city has exactly one outgoing route
    for i in range(n):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(n) if i != j) == 1,
            name=f"out_{i}",
        )

    # Each city has exactly one incoming route
    for j in range(n):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(n) if i != j) == 1,
            name=f"in_{j}",
        )

    # MTZ subtour elimination: for non-depot cities i, j (i != j)
    M = n
    for i in range(1, n):
        for j in range(1, n):
            if i != j:
                model.addConstr(
                    u[j] >= u[i] + 1 - M * (1 - x[i, j]),
                    name=f"mtz_{i}_{j}",
                )

    # Objective: minimize total travel cost
    model.setObjective(
        gp.quicksum(
            cost[i][j] * x[i, j]
            for i in range(n)
            for j in range(n)
            if i != j and cost[i][j] is not None
        ),
        GRB.MINIMIZE,
    )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": "failed"}