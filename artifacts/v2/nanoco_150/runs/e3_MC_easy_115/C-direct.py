import gurobipy as gp
from gurobipy import GRB

def solve(params):
    capacity = params["capacity"]
    cost = params["cost"]

    # Edge list in fixed order
    edges = [
        (0, 1), (0, 2), (0, 6), (0, 8),
        (1, 2), (1, 5),
        (2, 3), (2, 6),
        (3, 4),
        (4, 5),
        (5, 6),
        (6, 7), (6, 8),
        (7, 8)
    ]

    source = 0
    sink = 8
    num_edges = len(edges)

    model = gp.Model("min_cut")
    model.setParam("OutputFlag", 0)

    # x[i] = 1 if node i is on the source side of the cut
    x = model.addVars(9, vtype=GRB.BINARY, name="x")

    # y[e] = 1 if edge e crosses the cut (source-side -> sink-side)
    y = model.addVars(num_edges, vtype=GRB.BINARY, name="y")

    # Source must be on source side, sink on sink side
    model.addConstr(x[source] == 1, name="source_side")
    model.addConstr(x[sink] == 0, name="sink_side")

    # y[e] >= x[u] - x[v] for edge (u, v): if u is source-side and v is sink-side, y must be 1
    for idx, (u, v) in enumerate(edges):
        model.addConstr(y[idx] >= x[u] - x[v], name=f"cut_def_{idx}")

    # Minimize total capacity of cut edges
    model.setObjective(
        gp.quicksum(capacity[idx] * y[idx] for idx in range(num_edges)),
        GRB.MINIMIZE
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}