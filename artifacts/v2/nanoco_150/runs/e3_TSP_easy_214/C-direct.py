import gurobipy as gp
from gurobipy import GRB


def solve(params):
    dist = params["distance_matrix"]
    n = params["num_nodes"]  # 9 nodes: depot (0) + sites 1-8

    nodes = list(range(n))
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    model = gp.Model("TSP")
    model.setParam("OutputFlag", 0)

    # Binary arc variables
    x = model.addVars(arcs, vtype=GRB.BINARY, name="x")

    # MTZ subtour elimination auxiliary variables (for nodes 1..n-1)
    u = model.addVars(nodes[1:], lb=1.0, ub=float(n - 1), vtype=GRB.CONTINUOUS, name="u")

    # Objective: minimize total travel cost
    model.setObjective(
        gp.quicksum(dist[i][j] * x[i, j] for i, j in arcs),
        GRB.MINIMIZE
    )

    # Each node must be departed exactly once
    for i in nodes:
        model.addConstr(gp.quicksum(x[i, j] for j in nodes if j != i) == 1, name=f"out_{i}")

    # Each node must be arrived at exactly once
    for j in nodes:
        model.addConstr(gp.quicksum(x[i, j] for i in nodes if i != j) == 1, name=f"in_{j}")

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