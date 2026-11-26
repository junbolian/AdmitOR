import gurobipy as gp
from gurobipy import GRB

def solve(params):
    num_nodes = int(params["num_nodes"])
    
    # Build capacity dict from params
    capacity = {}
    for i in range(num_nodes):
        for j in range(num_nodes):
            if i != j:
                key = f"capacity_{i}_{j}"
                if key in params:
                    capacity[(i, j)] = params[key]
    
    source = 0
    sink = num_nodes - 1
    
    # Arcs with positive capacity
    arcs = [(i, j) for (i, j), cap in capacity.items() if cap > 0]
    
    model = gp.Model("max_flow")
    model.setParam("OutputFlag", 0)
    
    # Flow variables
    flow = model.addVars(arcs, lb=0.0, name="flow")
    
    # Capacity constraints
    for (i, j) in arcs:
        model.addConstr(flow[i, j] <= capacity[(i, j)], name=f"cap_{i}_{j}")
    
    # Flow conservation for intermediate nodes
    for node in range(num_nodes):
        if node == source or node == sink:
            continue
        in_flow = gp.quicksum(flow[i, j] for (i, j) in arcs if j == node)
        out_flow = gp.quicksum(flow[i, j] for (i, j) in arcs if i == node)
        model.addConstr(in_flow == out_flow, name=f"conservation_{node}")
    
    # Objective: maximize flow out of source
    obj = gp.quicksum(flow[i, j] for (i, j) in arcs if i == source)
    model.setObjective(obj, GRB.MAXIMIZE)
    
    model.optimize()
    
    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}