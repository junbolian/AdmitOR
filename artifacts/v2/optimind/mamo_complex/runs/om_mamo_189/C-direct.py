import gurobipy as gp
from gurobipy import GRB

def solve(params):
    # Build capacity dict from params
    # Edges: all (i,j) pairs where cap_i_j exists in params
    edges = []
    capacity = {}
    
    # Source is 0, sink is 8, nodes 0..8
    # Enumerate all possible edges from params
    nodes = list(range(9))
    for i in nodes:
        for j in nodes:
            if i == j:
                continue
            key = f"cap_{i}_{j}"
            if key in params:
                edges.append((i, j))
                capacity[(i, j)] = params[key]
    
    source = 0
    sink = 8
    
    model = gp.Model("max_flow")
    model.setParam("OutputFlag", 0)
    
    # Flow variables
    flow = {}
    for (i, j) in edges:
        flow[(i, j)] = model.addVar(lb=0.0, ub=capacity[(i, j)], name=f"f_{i}_{j}")
    
    model.update()
    
    # Objective: maximize flow into sink
    # (equivalently, maximize flow out of source)
    obj = gp.quicksum(flow[(i, sink)] for (i, j) in edges if j == sink)
    model.setObjective(obj, GRB.MAXIMIZE)
    
    # Flow conservation for intermediate nodes (not source, not sink)
    for node in nodes:
        if node == source or node == sink:
            continue
        in_flow = gp.quicksum(flow[(i, j)] for (i, j) in edges if j == node)
        out_flow = gp.quicksum(flow[(i, j)] for (i, j) in edges if i == node)
        model.addConstr(in_flow == out_flow, name=f"conserve_{node}")
    
    model.optimize()
    
    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}