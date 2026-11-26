import gurobipy as gp
from gurobipy import GRB


def solve(params):
    edge_list = [
        (1, 2, params["capacity_1_2"]),
        (1, 3, params["capacity_1_3"]),
        (2, 3, params["capacity_2_3"]),
        (2, 4, params["capacity_2_4"]),
        (3, 4, params["capacity_3_4"]),
    ]
    nodes = {1, 2, 3, 4}
    source, sink = 1, 4

    model = gp.Model("maxflow")
    model.Params.OutputFlag = 0

    flow = {}
    for (i, j, cap) in edge_list:
        flow[(i, j)] = model.addVar(lb=0, ub=cap, vtype=GRB.CONTINUOUS, name=f"f_{i}_{j}")

    arc_pairs = [(i, j) for (i, j, _) in edge_list]

    for n in nodes:
        if n in (source, sink):
            continue
        inflow = gp.quicksum(flow[(i, j)] for (i, j) in arc_pairs if j == n)
        outflow = gp.quicksum(flow[(i, j)] for (i, j) in arc_pairs if i == n)
        model.addConstr(inflow == outflow, name=f"balance_{n}")

    out_source = gp.quicksum(flow[(i, j)] for (i, j) in arc_pairs if i == source)
    in_sink = gp.quicksum(flow[(i, j)] for (i, j) in arc_pairs if j == sink)
    model.addConstr(out_source == in_sink, name="source_sink_balance")

    model.setObjective(out_source, GRB.MAXIMIZE)
    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(round(model.ObjVal)), "status": "optimal"}
    return {"objective": None, "status": f"status_{model.Status}"}