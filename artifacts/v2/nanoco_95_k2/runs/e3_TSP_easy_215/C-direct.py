import gurobipy as gp
from gurobipy import GRB

def solve(params):
    distance_matrix = params["distance_matrix"]
    # node_coordinates available but not needed for objective
    n = 9  # structural constant: number of nodes

    dist = {(i, j): distance_matrix[i][j] for i in range(n) for j in range(n)}

    model = gp.Model("TSP")
    model.setParam("OutputFlag", 0)

    # Binary decision variables: x[i,j] = 1 if truck travels from i to j
    x = model.addVars(n, n, vtype=GRB.BINARY, name="x")

    # MTZ subtour elimination variables: u[i] for i in 1..n-1
    u = model.addVars(n, vtype=GRB.CONTINUOUS, name="u")

    # Objective: minimize total distance
    model.setObjective(
        gp.quicksum(dist[i, j] * x[i, j] for i in range(n) for j in range(n) if i != j),
        GRB.MINIMIZE
    )

    # No self-loops
    for i in range(n):
        x[i, i].ub = 0

    # Each node is departed exactly once
    for i in range(n):
        model.addConstr(
            gp.quicksum(x[i, j] for j in range(n) if j != i) == 1,
            name=f"depart_{i}"
        )

    # Each node is arrived at exactly once
    for j in range(n):
        model.addConstr(
            gp.quicksum(x[i, j] for i in range(n) if i != j) == 1,
            name=f"arrive_{j}"
        )

    # MTZ subtour elimination constraints
    # u[0] = 0 (depot)
    model.addConstr(u[0] == 0, name="u_depot")

    for i in range(1, n):
        model.addConstr(u[i] >= 1, name=f"u_lb_{i}")
        model.addConstr(u[i] <= n - 1, name=f"u_ub_{i}")

    for i in range(1, n):
        for j in range(1, n):
            if i != j:
                model.addConstr(
                    u[i] - u[j] + (n - 1) * x[i, j] <= n - 2,
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
        return {"objective": None, "status": f"solver_status_{model.Status}"}