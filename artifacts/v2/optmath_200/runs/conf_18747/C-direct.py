import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n = params["num_cities"]
    u_lower = params["u_lower"]
    u_upper = params["u_upper"]

    # Build cost matrix from params
    cost = {}
    for i in range(n):
        for j in range(n):
            if i != j:
                cost[i, j] = params[f"travel_cost_{i}_{j}"]

    model = gp.Model("TSP")
    model.setParam("OutputFlag", 0)

    # Binary decision variables x[i,j]
    x = model.addVars(
        [(i, j) for i in range(n) for j in range(n) if i != j],
        vtype=GRB.BINARY,
        name="x"
    )

    # Auxiliary order variables u[i]
    u = model.addVars(range(n), lb=u_lower, ub=u_upper, vtype=GRB.CONTINUOUS, name="u")

    # Objective: minimize total travel cost
    model.setObjective(
        gp.quicksum(cost[i, j] * x[i, j] for i in range(n) for j in range(n) if i != j),
        GRB.MINIMIZE
    )

    # Each city must be entered exactly once
    for j in range(n):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(n) if i != j) == 1,
            name=f"enter_{j}"
        )

    # Each city must be departed exactly once
    for i in range(n):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(n) if i != j) == 1,
            name=f"depart_{i}"
        )

    # Miller-Tucker-Zemlin subtour elimination constraints
    # For non-depot cities i, j (i != 0, j != 0, i != j):
    # u[i] - u[j] + n * x[i,j] <= n - 1
    for i in range(1, n):
        for j in range(1, n):
            if i != j:
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