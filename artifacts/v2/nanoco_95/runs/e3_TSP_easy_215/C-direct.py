import gurobipy as gp
from gurobipy import GRB

def solve(params):
    distance_matrix = params["distance_matrix"]
    n = 9  # total nodes: 0 (warehouse) + 8 retail outlets
    nodes = list(range(n))

    # Build distance dict from matrix
    dist = {}
    for i in nodes:
        for j in nodes:
            dist[i, j] = distance_matrix[i][j]

    model = gp.Model("TSP_delivery")
    model.setParam("OutputFlag", 0)

    # Decision variables: x[i,j] = 1 if truck travels from i to j
    x = model.addVars(nodes, nodes, vtype=GRB.BINARY, name="x")

    # MTZ subtour elimination variables: u[i] for i in 1..8
    u = model.addVars(nodes, vtype=GRB.CONTINUOUS, name="u")

    # Objective: minimize total distance
    model.setObjective(
        gp.quicksum(dist[i, j] * x[i, j] for i in nodes for j in nodes if i != j),
        GRB.MINIMIZE
    )

    # No self-loops
    for i in nodes:
        model.addConstr(x[i, i] == 0, name=f"no_self_{i}")

    # Each node is departed exactly once
    for i in nodes:
        model.addConstr(
            gp.quicksum(x[i, j] for j in nodes if j != i) == 1,
            name=f"depart_{i}"
        )

    # Each node is arrived at exactly once
    for j in nodes:
        model.addConstr(
            gp.quicksum(x[i, j] for i in nodes if i != j) == 1,
            name=f"arrive_{j}"
        )

    # MTZ subtour elimination constraints (for non-depot nodes 1..8)
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