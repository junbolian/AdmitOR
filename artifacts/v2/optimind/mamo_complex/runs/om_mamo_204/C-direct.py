import gurobipy as gp
from gurobipy import GRB

def solve(params):
    capacity = params["capacity"]
    
    n = 8
    source = 0
    sink = 7
    
    model = gp.Model("max_flow")
    model.setParam("OutputFlag", 0)
    
    # Flow variables for each directed edge with positive capacity
    flow = {}
    for i in range(n):
        for j in range(n):
            cap = capacity[i][j]
            if cap > 0:
                flow[i, j] = model.addVar(lb=0.0, ub=cap, name=f"flow_{i}_{j}")
    
    model.update()
    
    # Flow conservation constraints for intermediate nodes
    for node in range(n):
        if node == source or node == sink:
            continue
        outflow = gp.quicksum(flow[i, j] for (i, j) in flow if i == node)
        inflow  = gp.quicksum(flow[i, j] for (i, j) in flow if j == node)
        model.addConstr(outflow == inflow, name=f"conservation_{node}")
    
    # Objective: maximize total flow out of source
    total_flow = gp.quicksum(flow[i, j] for (i, j) in flow if i == source) - \
                 gp.quicksum(flow[i, j] for (i, j) in flow if j == source)
    
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