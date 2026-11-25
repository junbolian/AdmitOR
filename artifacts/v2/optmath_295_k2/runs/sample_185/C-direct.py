import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n = int(params["num_cities"])
    pos_lb = params["position_lower_bound"]
    pos_ub = params["position_upper_bound"]

    # Build distance matrix from params
    dist = {}
    for i in range(n):
        for j in range(n):
            if i != j:
                dist[i, j] = params[f"distance_{i}_{j}"]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary route variables
    x = model.addVars(n, n, vtype=GRB.BINARY, name="x")
    for i in range(n):
        x[i, i].ub = 0  # no self-loops

    # Position variables for MTZ subtour elimination
    u = model.addVars(n, lb=pos_lb, ub=pos_ub, vtype=GRB.CONTINUOUS, name="u")

    # Objective: minimize total distance
    model.setObjective(
        gp.quicksum(dist[i, j] * x[i, j] for i in range(n) for j in range(n) if i != j),
        GRB.MINIMIZE
    )

    # Each city is left exactly once
    for i in range(n):
        model.addConstr(gp.quicksum(x[i, j] for j in range(n) if j != i) == 1, name=f"leave_{i}")

    # Each city is entered exactly once
    for j in range(n):
        model.addConstr(gp.quicksum(x[i, j] for i in range(n) if i != j) == 1, name=f"enter_{j}")

    # MTZ subtour elimination (applied to non-depot cities; depot is city 0)
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