import gurobipy as gp
from gurobipy import GRB

def solve(params):
    capacity_raw = params["capacity"]
    n = 9

    # Build capacity matrix - handle both flat list and list-of-lists
    cap = {}
    if isinstance(capacity_raw[0], (list, tuple)):
        for i in range(n):
            for j in range(n):
                cap[i, j] = capacity_raw[i][j]
    else:
        for i in range(n):
            for j in range(n):
                cap[i, j] = capacity_raw[i * n + j]

    model = gp.Model("max_flow")
    model.setParam("OutputFlag", 0)

    source = 0
    sink = 8

    # Flow variables for each arc with positive capacity
    flow = {}
    for i in range(n):
        for j in range(n):
            if cap[i, j] > 0:
                flow[i, j] = model.addVar(lb=0.0, ub=cap[i, j], name=f"f_{i}_{j}")

    # Maximize net flow into the sink
    model.setObjective(
        gp.quicksum(flow[i, sink] for i in range(n) if (i, sink) in flow)
        - gp.quicksum(flow[sink, j] for j in range(n) if (sink, j) in flow),
        GRB.MAXIMIZE
    )

    # Flow conservation for intermediate nodes
    for node in range(n):
        if node == source or node == sink:
            continue
        inflow = gp.quicksum(flow[i, node] for i in range(n) if (i, node) in flow)
        outflow = gp.quicksum(flow[node, j] for j in range(n) if (node, j) in flow)
        model.addConstr(inflow == outflow, name=f"conserve_{node}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}