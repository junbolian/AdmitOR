import gurobipy as gp
from gurobipy import GRB

def solve(params):
    # Build capacity dict from params
    nodes = list(range(8))
    
    # All directed edges (i, j) where i != j, excluding self-loops
    # and edges not present (capacity_1_5 etc. not in params means no edge)
    edges = [
        (0,1),(0,2),(0,3),(0,4),(0,5),(0,6),(0,7),
        (1,0),(1,2),(1,3),(1,4),(1,6),(1,7),
        (2,0),(2,3),(2,4),(2,5),(2,6),(2,7),
        (3,0),(3,1),(3,2),(3,4),(3,5),(3,6),(3,7),
        (4,0),(4,1),(4,2),(4,3),(4,5),(4,6),(4,7),
        (5,0),(5,1),(5,2),(5,3),(5,4),(5,6),(5,7),
        (6,0),(6,1),(6,2),(6,3),(6,4),(6,5),(6,7),
        (7,0),(7,1),(7,2),(7,3),(7,4),(7,5),(7,6),
    ]
    
    capacity = {}
    for (i, j) in edges:
        key = f"capacity_{i}_{j}"
        if key in params:
            capacity[(i, j)] = params[key]
        else:
            capacity[(i, j)] = 0

    source = 0
    sink = 7

    model = gp.Model("max_flow")
    model.setParam("OutputFlag", 0)

    # Flow variables
    flow = model.addVars(edges, lb=0.0, name="flow")

    # Objective: maximize flow out of source
    model.setObjective(
        gp.quicksum(flow[source, j] for j in nodes if (source, j) in flow) -
        gp.quicksum(flow[j, source] for j in nodes if (j, source) in flow),
        GRB.MAXIMIZE
    )

    # Capacity constraints
    for (i, j) in edges:
        model.addConstr(flow[i, j] <= capacity[(i, j)], name=f"cap_{i}_{j}")

    # Flow conservation for intermediate nodes
    for nd in nodes:
        if nd == source or nd == sink:
            continue
        in_flow = gp.quicksum(flow[i, nd] for i in nodes if (i, nd) in flow)
        out_flow = gp.quicksum(flow[nd, j] for j in nodes if (nd, j) in flow)
        model.addConstr(in_flow == out_flow, name=f"conserve_{nd}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}