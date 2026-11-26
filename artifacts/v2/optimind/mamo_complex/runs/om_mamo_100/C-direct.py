import gurobipy as gp
from gurobipy import GRB

def solve(params):
    capacity_matrix = params["capacity_matrix"]
    
    n = 9
    source = 0
    sink = 8
    
    # Build edge list with capacities
    edges = []
    cap = {}
    for i in range(n):
        for j in range(n):
            c = capacity_matrix[i][j]
            if c > 0:
                edges.append((i, j))
                cap[(i, j)] = c
    
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
    else:
        return {"objective": None, "status": f"status_{model.Status}"}