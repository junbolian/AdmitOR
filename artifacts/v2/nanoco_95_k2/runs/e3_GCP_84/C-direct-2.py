import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n_enclosures = 12
    edges = [
        (4, 9), (3, 7), (3, 10), (5, 7), (2, 11), (1, 9), (6, 8), (4, 5),
        (4, 8), (0, 1), (0, 7), (2, 4), (10, 11), (0, 4), (0, 10), (2, 7),
        (1, 5), (6, 7), (6, 10), (4, 7), (3, 8), (0, 9), (8, 10), (1, 7),
        (2, 6)
    ]

    # Upper bound on colors needed is n_enclosures; chromatic number >= 1
    max_colors = n_enclosures

    model = gp.Model("graph_coloring")
    model.setParam("OutputFlag", 0)

    # x[i, c] = 1 if enclosure i is assigned color c
    x = model.addVars(n_enclosures, max_colors, vtype=GRB.BINARY, name="x")
    # y[c] = 1 if color c is used by at least one enclosure
    y = model.addVars(max_colors, vtype=GRB.BINARY, name="y")

    # Each enclosure gets exactly one color
    for i in range(n_enclosures):
        model.addConstr(gp.quicksum(x[i, c] for c in range(max_colors)) == 1,
                        name=f"assign_{i}")

    # Adjacent enclosures cannot share the same color
    for (i, j) in edges:
        for c in range(max_colors):
            model.addConstr(x[i, c] + x[j, c] <= 1,
                            name=f"adj_{i}_{j}_{c}")

    # y[c] must be 1 if any enclosure uses color c
    for c in range(max_colors):
        for i in range(n_enclosures):
            model.addConstr(y[c] >= x[i, c], name=f"use_{c}_{i}")

    # Symmetry breaking: color c can only be used if c-1 is used
    for c in range(1, max_colors):
        model.addConstr(y[c] <= y[c - 1], name=f"sym_{c}")

    # Minimize number of distinct colors used
    model.setObjective(gp.quicksum(y[c] for c in range(max_colors)), GRB.MINIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}