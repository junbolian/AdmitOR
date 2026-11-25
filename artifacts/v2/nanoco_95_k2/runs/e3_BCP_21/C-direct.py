import gurobipy as gp
from gurobipy import GRB

def solve(params):
    edge_weights = params["edge_weights"]
    edges = [(0, 1), (0, 2), (1, 3), (1, 4), (1, 5),
             (2, 7), (3, 4), (3, 5), (4, 5), (4, 6), (4, 7), (5, 6)]
    n = 8
    weights = list(edge_weights)

    # Safe upper bound on any track assignment: a greedy placement along the
    # constraint graph never exceeds the sum of all edge weights.
    bigM = sum(weights) + 1

    model = gp.Model("channel_routing")
    model.Params.OutputFlag = 0

    t = model.addVars(n, vtype=GRB.INTEGER, lb=0, ub=bigM, name="t")
    span = model.addVar(vtype=GRB.INTEGER, lb=0, ub=bigM, name="span")
    b = model.addVars(len(edges), vtype=GRB.BINARY, name="b")

    model.addConstrs((t[i] <= span for i in range(n)), name="span_ub")

    for idx, (u, v) in enumerate(edges):
        d = weights[idx]
        model.addConstr(t[u] - t[v] >= d - bigM * (1 - b[idx]), name=f"lo_{idx}")
        model.addConstr(t[v] - t[u] >= d - bigM * b[idx], name=f"hi_{idx}")

    model.setObjective(span, GRB.MINIMIZE)
    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    return {"objective": None, "status": f"status_{model.status}"}