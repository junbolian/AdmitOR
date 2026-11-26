import gurobipy as gp
from gurobipy import GRB

def solve(params):
    # Build capacity dict from params
    nodes = list(range(8))
    # All directed edges (i != j, no self-loops)
    edges = [(i, j) for i in nodes for j in nodes if i != j]
    
    cap = {}
    for (i, j) in edges:
        key = f"cap_{i}_{j}"
        if key in params:
            cap[(i, j)] = params[key]
        else:
            cap[(i, j)] = 0.0

    source = 0
    sink = 7

    model = gp.Model("max_flow")
    model.setParam("OutputFlag", 0)

    # Flow variables for each directed edge
    flow = {}
    for (i, j) in edges:
        flow[(i, j)] = model.addVar(lb=0.0, ub=cap[(i, j)], name=f"flow_{i}_{j}")

    model.update()

    # Flow conservation for intermediate nodes
    for node in nodes:
        if node == source or node == sink:
            continue
        in_flow = gp.quicksum(flow[(i, node)] for (i, j) in edges if j == node)
        out_flow = gp.quicksum(flow[(node, j)] for (i, j) in edges if i == node)
        model.addConstr(in_flow == out_flow, name=f"conservation_{node}")

    # Objective: maximize flow out of source
    total_flow = gp.quicksum(flow[(source, j)] for (i, j) in edges if i == source) \
               - gp.quicksum(flow[(i, source)] for (i, j) in edges if j == source)

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