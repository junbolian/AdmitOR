import gurobipy as gp
from gurobipy import GRB

def solve(params):
    separation_weight = params["separation_weight"]

    # 8 nets, 12 constraints (fixed structure)
    nets = list(range(8))
    edges = [
        (0, 1), (0, 2), (1, 3), (1, 4), (1, 5),
        (2, 7), (3, 4), (3, 5), (4, 5), (4, 6),
        (4, 7), (5, 6)
    ]
    # separation_weight must have 12 entries, one per edge in order
    weights = separation_weight  # list of length 12

    # Upper bound on max track: sum of all weights is a safe upper bound
    T_ub = int(sum(weights)) + 1

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Track assignment for each net
    x = model.addVars(nets, lb=0, ub=T_ub, vtype=GRB.INTEGER, name="x")

    # Objective: minimize the maximum track assignment
    z = model.addVar(lb=0, ub=T_ub, vtype=GRB.INTEGER, name="z")
    model.setObjective(z, GRB.MINIMIZE)

    # z >= x[i] for all nets
    for i in nets:
        model.addConstr(z >= x[i], name=f"max_track_{i}")

    # Separation constraints: |x[u] - x[v]| >= d
    # Linearize with binary variable b[k]: if b[k]=1, x[u]-x[v] >= d; else x[v]-x[u] >= d
    b = model.addVars(len(edges), vtype=GRB.BINARY, name="b")
    M = T_ub + 1  # big-M

    for k, (u, v) in enumerate(edges):
        d = weights[k]
        # b[k]=1 => x[u] - x[v] >= d
        model.addConstr(x[u] - x[v] >= d - M * (1 - b[k]), name=f"sep_pos_{k}")
        # b[k]=0 => x[v] - x[u] >= d
        model.addConstr(x[v] - x[u] >= d - M * b[k], name=f"sep_neg_{k}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.TIME_LIMIT:
        return {"objective": None, "status": "time_limit"}
    else:
        return {"objective": None, "status": f"gurobi_status_{model.Status}"}