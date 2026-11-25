import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n_enclosures = 12
    edges = [
        (4, 9), (3, 7), (3, 10), (5, 7), (2, 11),
        (1, 9), (6, 8), (4, 5), (4, 8), (0, 1),
        (0, 7), (2, 4), (10, 11), (0, 4), (0, 10),
        (2, 7), (1, 5), (6, 7), (6, 10), (4, 7),
        (3, 8), (0, 9), (8, 10), (1, 7), (2, 6),
    ]
    max_colors = n_enclosures

    model = gp.Model("zoo_coloring")
    model.Params.OutputFlag = 0

    x = {}
    for i in range(n_enclosures):
        for c in range(max_colors):
            x[i, c] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{c}")

    y = {}
    for c in range(max_colors):
        y[c] = model.addVar(vtype=GRB.BINARY, name=f"y_{c}")

    for i in range(n_enclosures):
        model.addConstr(
            gp.quicksum(x[i, c] for c in range(max_colors)) == 1, name=f"assign_{i}"
        )

    for (i, j) in edges:
        for c in range(max_colors):
            model.addConstr(
                x[i, c] + x[j, c] <= 1, name=f"conflict_{i}_{j}_{c}"
            )

    for c in range(max_colors):
        for i in range(n_enclosures):
            model.addConstr(x[i, c] <= y[c], name=f"use_{i}_{c}")

    for c in range(1, max_colors):
        model.addConstr(y[c] <= y[c - 1], name=f"symbreak_{c}")

    model.setObjective(
        gp.quicksum(y[c] for c in range(max_colors)), GRB.MINIMIZE
    )
    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    return {"objective": None, "status": f"status_{model.status}"}