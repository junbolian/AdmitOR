import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cities = ["E", "F", "G", "H"]
    n = len(cities)
    idx = {c: i for i, c in enumerate(cities)}

    cost = {}
    for (a, b) in [("E","F"),("E","G"),("E","H"),("F","E"),("F","G"),("F","H"),
                   ("G","E"),("G","F"),("G","H"),("H","E"),("H","F"),("H","G")]:
        cost[(idx[a], idx[b])] = params[f"cost_{a}_{b}"]

    model = gp.Model("TSP")
    model.setParam("OutputFlag", 0)

    x = model.addVars(n, n, vtype=GRB.BINARY, name="x")

    # No self-loops
    for i in range(n):
        x[i, i].ub = 0

    # Objective
    model.setObjective(
        gp.quicksum(cost[(i, j)] * x[i, j] for i in range(n) for j in range(n) if i != j),
        GRB.MINIMIZE
    )

    # Each city is left exactly once
    for i in range(n):
        model.addConstr(gp.quicksum(x[i, j] for j in range(n) if j != i) == 1, name=f"out_{i}")

    # Each city is entered exactly once
    for j in range(n):
        model.addConstr(gp.quicksum(x[i, j] for i in range(n) if i != j) == 1, name=f"in_{j}")

    # MTZ subtour elimination
    u = model.addVars(n, lb=0.0, ub=n - 1.0, vtype=GRB.CONTINUOUS, name="u")
    for i in range(1, n):
        for j in range(1, n):
            if i != j:
                model.addConstr(u[i] - u[j] + n * x[i, j] <= n - 1, name=f"mtz_{i}_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}