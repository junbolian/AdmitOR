import gurobipy as gp
from gurobipy import GRB

def solve(params):
    # Define the network structure: all directed edges (i, j) where i != j
    # and capacity exists (note: some pairs have 0 capacity meaning no link,
    # but we include all pairs that appear in params)
    
    n_hubs = 8
    source = 0
    sink = 7
    
    # Build capacity dict from params
    # Edges that appear in params (some pairs are missing, meaning capacity = 0)
    capacity = {}
    
    # All edges listed in params
    edge_keys = [
        (0,1),(0,2),(0,3),(0,4),(0,5),(0,6),(0,7),
        (1,0),(1,2),(1,3),(1,4),(1,5),(1,6),(1,7),
        (2,0),(2,1),(2,3),(2,4),(2,5),(2,6),(2,7),
        (3,0),(3,1),(3,2),(3,4),(3,5),(3,6),
        (4,0),(4,1),(4,2),(4,5),(4,6),(4,7),
        (5,0),(5,1),(5,2),(5,3),(5,4),(5,6),(5,7),
        (6,0),(6,1),(6,2),(6,3),(6,4),(6,5),(6,7),
    ]
    
    for (i, j) in edge_keys:
        key = f"capacity_{i}_{j}"
        capacity[(i, j)] = params[key]
    
    # Create model
    model = gp.Model("max_flow")
    model.setParam("OutputFlag", 0)
    
    # Flow variables for each edge
    flow = {}
    for (i, j) in edge_keys:
        flow[(i, j)] = model.addVar(lb=0.0, ub=capacity[(i, j)], name=f"f_{i}_{j}")
    
    # Objective: maximize flow out of source
    model.setObjective(
        gp.quicksum(flow[(source, j)] for (i, j) in edge_keys if i == source),
        GRB.MAXIMIZE
    )
    
    # Flow conservation constraints for intermediate nodes
    for node in range(n_hubs):
        if node == source or node == sink:
            continue
        inflow = gp.quicksum(flow[(i, j)] for (i, j) in edge_keys if j == node)
        outflow = gp.quicksum(flow[(i, j)] for (i, j) in edge_keys if i == node)
        model.addConstr(inflow == outflow, name=f"conservation_{node}")
    
    model.optimize()
    
    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}