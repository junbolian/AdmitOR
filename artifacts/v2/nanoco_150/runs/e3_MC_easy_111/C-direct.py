import gurobipy as gp
from gurobipy import GRB

def solve(params):
    edges = [
        (0, 1), (1, 2), (1, 7), (2, 3), (2, 6),
        (3, 4), (3, 8), (3, 9), (4, 5), (4, 8),
        (5, 6), (6, 7), (7, 8), (7, 9), (8, 9)
    ]

    capacity = {
        (0, 1): params["capacity_0_1"],
        (1, 2): params["capacity_1_2"],
        (1, 7): params["capacity_1_7"],
        (2, 3): params["capacity_2_3"],
        (2, 6): params["capacity_2_6"],
        (3, 4): params["capacity_3_4"],
        (3, 8): params["capacity_3_8"],
        (3, 9): params["capacity_3_9"],
        (4, 5): params["capacity_4_5"],
        (4, 8): params["capacity_4_8"],
        (5, 6): params["capacity_5_6"],
        (6, 7): params["capacity_6_7"],
        (7, 8): params["capacity_7_8"],
        (7, 9): params["capacity_7_9"],
        (8, 9): params["capacity_8_9"],
    }

    source = 0
    sink = 9
    nodes = list(range(10))

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # x[i] = 1 if node i is on the source side, 0 if on the sink side
    x = model.addVars(nodes, vtype=GRB.BINARY, name="x")

    # y[i,j] = 1 if edge (i,j) is in the cut (i on source side, j on sink side)
    y = model.addVars(edges, vtype=GRB.BINARY, name="y")

    # Source must be on source side, sink on sink side
    model.addConstr(x[source] == 1, name="fix_source")
    model.addConstr(x[sink] == 0, name="fix_sink")

    # y[i,j] >= x[i] - x[j]: edge is cut if i is on source side and j is on sink side
    for (i, j) in edges:
        model.addConstr(y[i, j] >= x[i] - x[j], name=f"cut_{i}_{j}")

    # Minimize total cut capacity
    model.setObjective(
        gp.quicksum(capacity[e] * y[e] for e in edges),
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