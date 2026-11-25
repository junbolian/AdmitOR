import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n = params["num_nodes"]  # 10
    dist = params["distance_matrix"]

    nodes = list(range(n))
    # All arcs except self-loops
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    model = gp.Model("tsp_waste")
    model.setParam("OutputFlag", 0)

    # Binary arc selection variables
    x = model.addVars(arcs, vtype=GRB.BINARY, name="x")

    # Subtour elimination auxiliary variables (MTZ formulation)
    # u[i] for i in 1..n-1: position of node i in the tour
    u = model.addVars(nodes[1:], lb=1, ub=n - 1, vtype=GRB.CONTINUOUS, name="u")

    # Objective: minimize total distance
    model.setObjective(
        gp.quicksum(dist[i][j] * x[i, j] for i, j in arcs),
        GRB.MINIMIZE
    )

    # Each node must be entered exactly once
    for j in nodes:
        model.addConstr(gp.quicksum(x[i, j] for i in nodes if i != j) == 1, name=f"enter_{j}")

    # Each node must be exited exactly once
    for i in nodes:
        model.addConstr(gp.quicksum(x[i, j] for j in nodes if j != i) == 1, name=f"exit_{i}")

    # MTZ subtour elimination constraints
    for i in nodes[1:]:
        for j in nodes[1:]:
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
    elif model.Status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}