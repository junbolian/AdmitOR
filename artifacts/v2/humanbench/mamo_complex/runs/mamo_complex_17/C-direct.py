import gurobipy as gp
from gurobipy import GRB

def solve(params):
    capacity_matrix = params["capacity_matrix"]
    num_centers = params["num_centers"]
    source_node = params["source_node"]
    sink_node = params["sink_node"]

    nodes = range(num_centers)

    # Build capacity dict c[i][j], treating diagonal as 0
    # capacity_matrix[i] has num_centers-1 entries (excluding i itself)
    cap = {}
    for i in nodes:
        cap[i] = {}
        row = capacity_matrix[i]
        col_idx = 0
        for j in nodes:
            if j == i:
                cap[i][j] = 0
            else:
                cap[i][j] = row[col_idx]
                col_idx += 1

    model = gp.Model("max_flow")
    model.setParam("OutputFlag", 0)

    # Flow variables for each directed edge with positive capacity
    flow = {}
    for i in nodes:
        for j in nodes:
            if i != j and cap[i][j] > 0:
                flow[i, j] = model.addVar(lb=0.0, ub=cap[i][j], name=f"f_{i}_{j}")

    model.update()

    # Objective: maximize flow into sink
    sink_inflow = gp.quicksum(
        flow[i, sink_node] for i in nodes if (i, sink_node) in flow
    )
    model.setObjective(sink_inflow, GRB.MAXIMIZE)

    # Flow conservation for all nodes except source and sink
    for n in nodes:
        if n == source_node or n == sink_node:
            continue
        inflow = gp.quicksum(flow[i, n] for i in nodes if (i, n) in flow)
        outflow = gp.quicksum(flow[n, j] for j in nodes if (n, j) in flow)
        model.addConstr(inflow == outflow, name=f"conservation_{n}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}