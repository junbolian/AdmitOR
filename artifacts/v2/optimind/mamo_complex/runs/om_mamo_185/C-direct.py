import gurobipy as gp
from gurobipy import GRB

def solve(params):
    capacity = params["capacity"]
    
    n = 8
    source = 0
    sink = 7
    
    # Build list of valid arcs (where capacity > 0)
    arcs = []
    cap = {}
    for i in range(n):
        for j in range(n):
            c = capacity[i][j]
            if c > 0:
                arcs.append((i, j))
                cap[(i, j)] = c
    
    model = gp.Model("max_flow")
    model.setParam("OutputFlag", 0)
    
    # Flow variables for each arc
    flow = model.addVars(arcs, lb=0.0, name="flow")
    
    # Capacity constraints
    for (i, j) in arcs:
        model.addConstr(flow[i, j] <= cap[(i, j)], name=f"cap_{i}_{j}")
    
    # Flow conservation for intermediate nodes
    for node in range(n):
        if node == source or node == sink:
            continue
        in_flow = gp.quicksum(flow[i, j] for (i, j) in arcs if j == node)
        out_flow = gp.quicksum(flow[i, j] for (i, j) in arcs if i == node)
        model.addConstr(in_flow == out_flow, name=f"conservation_{node}")
    
    # Objective: maximize flow out of source
    total_flow = gp.quicksum(flow[i, j] for (i, j) in arcs if i == source)
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