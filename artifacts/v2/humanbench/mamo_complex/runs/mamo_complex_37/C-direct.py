import gurobipy as gp
from gurobipy import GRB

def solve(params):
    capacities = params["capacities"]
    
    n = 8
    source = 0
    sink = 7
    
    pairs = [(i, j) for i in range(n) for j in range(n) if i != j]
    cap = {pairs[k]: capacities[k] for k in range(len(pairs))}
    
    model = gp.Model("max_flow")
    model.setParam("OutputFlag", 0)
    
    flow = model.addVars(pairs, lb=0.0, name="flow")
    
    for (i, j) in pairs:
        model.addConstr(flow[i, j] <= cap[(i, j)], name=f"cap_{i}_{j}")
    
    for node in range(n):
        if node == source or node == sink:
            continue
        inflow = gp.quicksum(flow[i, node] for i in range(n) if i != node)
        outflow = gp.quicksum(flow[node, j] for j in range(n) if j != node)
        model.addConstr(inflow == outflow, name=f"conservation_{node}")
    
    # Net flow out of source
    out_of_source = gp.quicksum(flow[source, j] for j in range(n) if j != source)
    into_source = gp.quicksum(flow[i, source] for i in range(n) if i != source)
    obj = out_of_source - into_source
    model.setObjective(obj, GRB.MAXIMIZE)
    
    model.optimize()
    
    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}