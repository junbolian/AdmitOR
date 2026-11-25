import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cost_matrix = params["cost_matrix"]
    max_degree = params["max_degree"]
    n = 15

    model = gp.Model("dcmst")
    model.Params.OutputFlag = 0

    edges = [(i, j) for i in range(n) for j in range(i + 1, n)]
    x = {(i, j): model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")
         for (i, j) in edges}

    f = {(i, j): model.addVar(lb=0, vtype=GRB.CONTINUOUS, name=f"f_{i}_{j}")
         for i in range(n) for j in range(n) if i != j}

    model.setObjective(
        gp.quicksum(cost_matrix[i][j] * x[i, j] for (i, j) in edges),
        GRB.MINIMIZE,
    )

    # A tree on n nodes has exactly n-1 edges
    model.addConstr(gp.quicksum(x[i, j] for (i, j) in edges) == n - 1)

    # Degree constraint at every node
    for i in range(n):
        incident = [x[min(i, j), max(i, j)] for j in range(n) if i != j]
        model.addConstr(gp.quicksum(incident) <= max_degree)

    # Single-commodity flow from a root to enforce connectivity (and thus a tree
    # given exactly n-1 edges): root sends n-1 units, every other node consumes 1
    root = 0
    model.addConstr(
        gp.quicksum(f[root, j] for j in range(n) if j != root)
        - gp.quicksum(f[j, root] for j in range(n) if j != root)
        == n - 1
    )
    for k in range(n):
        if k == root:
            continue
        model.addConstr(
            gp.quicksum(f[k, j] for j in range(n) if j != k)
            - gp.quicksum(f[j, k] for j in range(n) if j != k)
            == -1
        )

    # Flow can only traverse selected edges
    for (i, j) in edges:
        model.addConstr(f[i, j] + f[j, i] <= (n - 1) * x[i, j])

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": "failed"}