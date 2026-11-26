import gurobipy as gp
from gurobipy import GRB

def solve(params):
    capacity_flat = params["capacity"]
    
    n = 8
    source = 0
    sink = 7
    
    # Build adjacency matrix from flat list (row-major, omitting diagonal)
    # The flat list has n*(n-1) entries: for each row i, columns j != i
    cap = {}
    idx = 0
    for i in range(n):
        for j in range(n):
            if i != j:
                cap[(i, j)] = capacity_flat[idx]
                idx += 1
    
    # Collect edges with positive capacity
    edges = [(i, j) for (i, j), c in cap.items() if c > 0]
    
    model = gp.Model("max_flow")
    model.setParam("OutputFlag", 0)
    
    # Flow variables
    flow = model.addVars(edges, lb=0.0, name="flow")
    
    # Capacity constraints
    for (i, j) in edges:
        model.addConstr(flow[i, j] <= cap[(i, j)], name=f"cap_{i}_{j}")
    
    # Flow conservation for intermediate nodes
    for node in range(n):
        if node == source or node == sink:
            continue
        inflow = gp.quicksum(flow[i, j] for (i, j) in edges if j == node)
        outflow = gp.quicksum(flow[i, j] for (i, j) in edges if i == node)
        model.addConstr(inflow == outflow, name=f"conserve_{node}")
    
    # Objective: maximize flow out of source
    total_flow = gp.quicksum(flow[i, j] for (i, j) in edges if i == source) - \
                 gp.quicksum(flow[i, j] for (i, j) in edges if j == source)
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