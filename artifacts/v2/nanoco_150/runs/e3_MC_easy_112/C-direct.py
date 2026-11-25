import gurobipy as gp
from gurobipy import GRB

def solve(params):
    arc_capacities = params["arc_capacities"]

    arcs = [
        (0, 1), (0, 6), (0, 8),
        (1, 2), (2, 3), (2, 7),
        (3, 4), (4, 5), (4, 7), (4, 8),
        (5, 6), (6, 7), (6, 8),
        (7, 8), (8, 9)
    ]

    source = 0
    sink = 9
    n_nodes = 10

    cap = {arcs[i]: arc_capacities[i] for i in range(len(arcs))}

    model = gp.Model("min_cut")
    model.setParam("OutputFlag", 0)

    # x[i] = 1 if node i is on the source side of the cut
    x = model.addVars(n_nodes, vtype=GRB.BINARY, name="x")

    # y[i,j] = 1 if arc (i,j) crosses the cut (i on source side, j on sink side)
    y = {(i, j): model.addVar(vtype=GRB.BINARY, name=f"y_{i}_{j}") for (i, j) in arcs}

    # Source must be on source side, sink on sink side
    model.addConstr(x[source] == 1, name="source_side")
    model.addConstr(x[sink] == 0, name="sink_side")

    # y[i,j] >= x[i] - x[j]: arc (i,j) is cut if i is on source side and j on sink side
    for (i, j) in arcs:
        model.addConstr(y[(i, j)] >= x[i] - x[j], name=f"cut_{i}_{j}")

    # Minimize total capacity of cut arcs
    model.setObjective(
        gp.quicksum(cap[(i, j)] * y[(i, j)] for (i, j) in arcs),
        GRB.MINIMIZE
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}