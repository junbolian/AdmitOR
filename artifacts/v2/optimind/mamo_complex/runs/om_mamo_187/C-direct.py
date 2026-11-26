import gurobipy as gp
from gurobipy import GRB

def solve(params):
    # Build capacity dict from params
    nodes = list(range(9))
    # All directed edges (i != j), node 8 has no outgoing edges based on problem description
    edges = [(i, j) for i in nodes for j in nodes if i != j and not (i == 8)]
    
    # Build capacity lookup
    capacity = {}
    for (i, j) in edges:
        key = f"capacity_{i}_{j}"
        if key in params:
            capacity[(i, j)] = params[key]
        else:
            capacity[(i, j)] = 0

    model = gp.Model("max_flow")
    model.setParam("OutputFlag", 0)

    # Flow variables
    flow = model.addVars(edges, lb=0.0, name="flow")

    # Capacity constraints
    for (i, j) in edges:
        model.addConstr(flow[i, j] <= capacity[(i, j)], name=f"cap_{i}_{j}")

    # Flow conservation for intermediate nodes (not source=0, not sink=8)
    for node in nodes:
        if node == 0 or node == 8:
            continue
        inflow = gp.quicksum(flow[i, node] for (i, j) in edges if j == node)
        outflow = gp.quicksum(flow[node, j] for (i, j) in edges if i == node)
        model.addConstr(inflow == outflow, name=f"conserve_{node}")

    # Objective: maximize flow out of source node 0
    total_flow = gp.quicksum(flow[0, j] for (i, j) in edges if i == 0)
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