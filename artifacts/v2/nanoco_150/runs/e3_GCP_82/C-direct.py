import gurobipy as gp
from gurobipy import GRB

def solve(params):
    # Graph coloring problem: minimize number of colors (frequencies) used
    # 12 towers, 17 edges
    num_towers = 12
    edges = [
        (0, 1), (0, 4), (5, 8), (4, 9), (6, 9), (6, 8), (3, 10), (5, 7),
        (0, 6), (6, 7), (8, 9), (2, 6), (0, 5), (9, 11), (0, 8), (2, 11), (0, 11)
    ]

    # Upper bound on colors needed: num_towers (trivial), but we can use a tighter bound.
    # Maximum degree in the graph gives a practical upper bound.
    degree = [0] * num_towers
    for u, v in edges:
        degree[u] += 1
        degree[v] += 1
    max_degree = max(degree)
    # Brooks' theorem: colors needed <= max_degree + 1
    num_colors = max_degree + 1  # safe upper bound

    towers = range(num_towers)
    colors = range(num_colors)

    model = gp.Model("graph_coloring")
    model.setParam("OutputFlag", 0)

    # x[i, c] = 1 if tower i is assigned color c
    x = model.addVars(towers, colors, vtype=GRB.BINARY, name="x")

    # y[c] = 1 if color c is used by at least one tower
    y = model.addVars(colors, vtype=GRB.BINARY, name="y")

    # Objective: minimize number of colors used
    model.setObjective(gp.quicksum(y[c] for c in colors), GRB.MINIMIZE)

    # Each tower must be assigned exactly one color
    for i in towers:
        model.addConstr(gp.quicksum(x[i, c] for c in colors) == 1, name=f"assign_{i}")

    # Adjacent towers must not share the same color
    for u, v in edges:
        for c in colors:
            model.addConstr(x[u, c] + x[v, c] <= 1, name=f"edge_{u}_{v}_{c}")

    # Link x and y: if tower i uses color c, color c must be active
    for i in towers:
        for c in colors:
            model.addConstr(x[i, c] <= y[c], name=f"link_{i}_{c}")

    # Symmetry breaking: color c can only be used if color c-1 is used
    for c in range(1, num_colors):
        model.addConstr(y[c] <= y[c - 1], name=f"sym_{c}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}