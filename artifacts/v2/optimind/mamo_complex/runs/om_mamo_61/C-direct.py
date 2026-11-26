import gurobipy as gp
from gurobipy import GRB

def solve(params):
    capacity = params["capacity"]
    
    n = 9
    source = 0
    sink = 8
    
    # Build list of valid arcs (where capacity > 0)
    arcs = [(i, j) for i in range(n) for j in range(n) if i != j and capacity[i][j] > 0]
    
    model = gp.Model("max_flow")
    model.setParam("OutputFlag", 0)
    
    # Flow variables for each arc
    flow = model.addVars(arcs, lb=0.0, name="flow")
    
    # Capacity constraints
    for (i, j) in arcs:
        model.addConstr(flow[i, j] <= capacity[i][j], name=f"cap_{i}_{j}")
    
    # Flow conservation for intermediate nodes
    for node in range(n):
        if node == source or node == sink:
            continue
        inflow = gp.quicksum(flow[i, node] for (i, j) in arcs if j == node)
        outflow = gp.quicksum(flow[node, j] for (i, j) in arcs if i == node)
        model.addConstr(inflow == outflow, name=f"conserve_{node}")
    
    # Objective: maximize net outflow from source
    net_outflow = (
        gp.quicksum(flow[source, j] for (i, j) in arcs if i == source) -
        gp.quicksum(flow[i, source] for (i, j) in arcs if j == source)
    )
    model.setObjective(net_outflow, GRB.MAXIMIZE)
    
    model.optimize()
    
    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}