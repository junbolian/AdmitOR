import gurobipy as gp
from gurobipy import GRB

def solve(params):
    num_substances = params["num_substances"]
    num_incompatibility_edges = params["num_incompatibility_edges"]
    edge_list = params["edge_list"]

    # Upper bound on colors needed (worst case: num_substances colors)
    max_colors = num_substances

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i][k] = 1 if substance i is assigned to section k
    x = {}
    for i in range(num_substances):
        for k in range(max_colors):
            x[i, k] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{k}")

    # y[k] = 1 if section k is used
    y = {}
    for k in range(max_colors):
        y[k] = model.addVar(vtype=GRB.BINARY, name=f"y_{k}")

    # Objective: minimize number of sections used
    model.setObjective(gp.quicksum(y[k] for k in range(max_colors)), GRB.MINIMIZE)

    # Each substance assigned to exactly one section
    for i in range(num_substances):
        model.addConstr(gp.quicksum(x[i, k] for k in range(max_colors)) == 1)

    # Incompatible substances cannot share a section
    for edge in edge_list:
        u, v = edge[0], edge[1]
        for k in range(max_colors):
            model.addConstr(x[u, k] + x[v, k] <= 1)

    # If substance i is in section k, section k must be active
    for i in range(num_substances):
        for k in range(max_colors):
            model.addConstr(x[i, k] <= y[k])

    # Symmetry breaking: section k can only be used if section k-1 is used
    for k in range(1, max_colors):
        model.addConstr(y[k] <= y[k - 1])

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}