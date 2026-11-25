import gurobipy as gp
from gurobipy import GRB

def solve(params):
    dist = params["distance_matrix"]
    n = 10
    nodes = list(range(n))

    model = gp.Model("tsp")
    model.setParam("OutputFlag", 0)

    # x[i,j] = 1 if van travels from i to j
    x = model.addVars(nodes, nodes, vtype=GRB.BINARY, name="x")

    # u[i] = position of node i in tour (MTZ formulation), for i in 1..n-1
    u = model.addVars(nodes, vtype=GRB.CONTINUOUS, name="u")

    # No self-loops
    for i in nodes:
        model.addConstr(x[i, i] == 0)

    # Each node is departed exactly once
    for i in nodes:
        model.addConstr(gp.quicksum(x[i, j] for j in nodes) == 1)

    # Each node is arrived at exactly once
    for j in nodes:
        model.addConstr(gp.quicksum(x[i, j] for i in nodes) == 1)

    # MTZ subtour elimination for nodes 1..n-1
    for i in range(1, n):
        for j in range(1, n):
            if i != j:
                model.addConstr(u[i] - u[j] + n * x[i, j] <= n - 1)

    # Bound u values
    for i in range(1, n):
        model.addConstr(u[i] >= 1)
        model.addConstr(u[i] <= n - 1)

    # Objective: minimize total distance
    model.setObjective(
        gp.quicksum(dist[i][j] * x[i, j] for i in nodes for j in nodes),
        GRB.MINIMIZE
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