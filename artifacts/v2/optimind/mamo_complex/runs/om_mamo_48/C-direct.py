import gurobipy as gp
from gurobipy import GRB

def solve(params):
    # Build capacity dictionary from params
    # Node 0 is source, Node 7 is sink
    # Edges present in the problem
    edges = [
        (0,1), (0,2), (0,3), (0,4), (0,5), (0,6), (0,7),
        (1,2), (1,3), (1,4), (1,5), (1,6), (1,7),
        (2,1), (2,3), (2,4), (2,5), (2,6), (2,7),
        (3,1), (3,2), (3,4), (3,5), (3,7),
        (4,1), (4,2), (4,3), (4,5), (4,6), (4,7),
        (5,1), (5,2), (5,3), (5,4), (5,6), (5,7),
        (6,1), (6,2), (6,3), (6,4), (6,5), (6,7),
        (7,1), (7,2), (7,3), (7,4), (7,5), (7,6),
    ]

    capacity = {}
    for (i, j) in edges:
        key = f"cap_{i}_{j}"
        capacity[(i, j)] = params[key]

    source = 0
    sink = 7
    nodes = list(range(8))

    model = gp.Model("max_flow")
    model.setParam("OutputFlag", 0)

    # Flow variables
    flow = {}
    for (i, j) in edges:
        flow[(i, j)] = model.addVar(lb=0.0, ub=capacity[(i, j)], name=f"f_{i}_{j}")

    # Objective: maximize flow out of source
    model.setObjective(
        gp.quicksum(flow[(0, j)] for j in nodes if (0, j) in flow),
        GRB.MAXIMIZE
    )

    # Flow conservation for intermediate nodes
    for node in nodes:
        if node == source or node == sink:
            continue
        in_flow = gp.quicksum(flow[(i, node)] for (i, j) in edges if j == node)
        out_flow = gp.quicksum(flow[(node, j)] for (i, j) in edges if i == node)
        model.addConstr(in_flow == out_flow, name=f"conservation_{node}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}