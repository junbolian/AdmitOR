import gurobipy as gp
from gurobipy import GRB

def solve(params):
    capacities = params["capacities"]
    
    n = 7
    source = 0
    sink = 6
    
    model = gp.Model("max_flow")
    model.setParam("OutputFlag", 0)
    
    # Build edge list from capacities matrix
    # capacities is indexed as capacities[i][j]
    flow = {}
    for i in range(n):
        for j in range(n):
            cap = capacities[i][j]
            if cap > 0:
                flow[i, j] = model.addVar(lb=0.0, ub=cap, name=f"f_{i}_{j}")
    
    model.update()
    
    # Flow conservation constraints for intermediate nodes
    for node in range(n):
        if node == source or node == sink:
            continue
        in_flow = gp.quicksum(flow[i, j] for (i, j) in flow if j == node)
        out_flow = gp.quicksum(flow[i, j] for (i, j) in flow if i == node)
        model.addConstr(in_flow == out_flow, name=f"conservation_{node}")
    
    # Objective: maximize flow out of source
    total_flow = gp.quicksum(flow[source, j] for (i, j) in flow if i == source for _ in [None])
    # Rewrite cleanly
    total_flow = gp.quicksum(flow[i, j] for (i, j) in flow if i == source)
    
    model.setObjective(total_flow, GRB.MAXIMIZE)
    
    model.optimize()
    
    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}