import gurobipy as gp
from gurobipy import GRB

def solve(params):
    # Number of hubs
    N = 8
    source = 0
    sink = 7

    # Build capacity dict from params; missing edges have capacity 0
    capacity = {}
    for i in range(N):
        for j in range(N):
            if i != j:
                key = f"capacity_{i}_{j}"
                capacity[(i, j)] = params.get(key, 0)

    # Edges with positive capacity
    edges = [(i, j) for (i, j), c in capacity.items() if c > 0]

    model = gp.Model("max_flow")
    model.setParam("OutputFlag", 0)

    # Flow variables
    flow = model.addVars(edges, lb=0.0, name="flow")

    # Capacity constraints
    for (i, j) in edges:
        model.addConstr(flow[i, j] <= capacity[(i, j)], name=f"cap_{i}_{j}")

    # Flow conservation for intermediate nodes
    for node in range(N):
        if node == source or node == sink:
            continue
        in_flow = gp.quicksum(flow[i, j] for (i, j) in edges if j == node)
        out_flow = gp.quicksum(flow[i, j] for (i, j) in edges if i == node)
        model.addConstr(in_flow == out_flow, name=f"conserve_{node}")

    # Objective: maximize flow out of source
    total_flow = gp.quicksum(flow[i, j] for (i, j) in edges if i == source)
    model.setObjective(total_flow, GRB.MAXIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}