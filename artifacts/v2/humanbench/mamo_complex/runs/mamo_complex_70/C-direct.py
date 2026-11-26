import gurobipy as gp
from gurobipy import GRB

def solve(params):
    # Define the network structure
    # Nodes: 0-8, Source: 0, Sink: 8
    # Edges and their capacities from params
    
    edges = [
        (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6), (0, 7), (0, 8),
        (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7), (1, 8),
        (2, 1), (2, 3), (2, 4), (2, 5), (2, 6), (2, 7), (2, 8),
        (3, 1), (3, 2), (3, 4), (3, 5), (3, 6), (3, 7), (3, 8),
        (4, 1), (4, 2), (4, 3), (4, 5), (4, 6), (4, 8),
        (5, 1), (5, 2), (5, 3), (5, 4), (5, 6), (5, 7), (5, 8),
        (6, 1), (6, 2), (6, 3), (6, 4), (6, 5), (6, 7), (6, 8),
        (7, 1), (7, 2), (7, 3), (7, 4), (7, 5), (7, 6), (7, 8),
        (8, 1), (8, 2), (8, 3), (8, 4), (8, 5), (8, 6), (8, 7),
    ]
    
    capacity = {}
    for (i, j) in edges:
        key = f"capacity_{i}_{j}"
        capacity[(i, j)] = params[key]
    
    source = 0
    sink = 8
    nodes = list(range(9))
    
    model = gp.Model("max_flow")
    model.setParam("OutputFlag", 0)
    
    # Flow variables
    flow = {}
    for (i, j) in edges:
        flow[(i, j)] = model.addVar(lb=0.0, ub=capacity[(i, j)], name=f"flow_{i}_{j}")
    
    model.update()
    
    # Flow conservation constraints for intermediate nodes (1-7)
    for node in nodes:
        if node == source or node == sink:
            continue
        in_flow = gp.quicksum(flow[(i, j)] for (i, j) in edges if j == node)
        out_flow = gp.quicksum(flow[(i, j)] for (i, j) in edges if i == node)
        model.addConstr(in_flow == out_flow, name=f"flow_conservation_{node}")
    
    # Objective: maximize flow into the sink
    total_flow = gp.quicksum(flow[(i, j)] for (i, j) in edges if j == sink)
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