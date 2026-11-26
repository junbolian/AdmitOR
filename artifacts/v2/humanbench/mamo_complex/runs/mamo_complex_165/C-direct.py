import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n = 6
    source = 0
    sink = 5

    # Build capacity dict from params
    capacity = {}
    for i in range(n):
        for j in range(n):
            if i != j:
                key = f"capacity_{i}_{j}"
                if key in params:
                    capacity[(i, j)] = params[key]

    edges = list(capacity.keys())

    model = gp.Model("max_flow")
    model.setParam("OutputFlag", 0)

    # Flow variables
    flow = model.addVars(edges, lb=0.0, name="flow")

    # Capacity constraints
    for (i, j) in edges:
        model.addConstr(flow[(i, j)] <= capacity[(i, j)], name=f"cap_{i}_{j}")

    # Flow conservation for intermediate nodes
    for node in range(n):
        if node == source or node == sink:
            continue
        in_flow = gp.quicksum(flow[(i, node)] for (i, j) in edges if j == node)
        out_flow = gp.quicksum(flow[(node, j)] for (i, j) in edges if i == node)
        model.addConstr(in_flow == out_flow, name=f"conservation_{node}")

    # Objective: maximize flow out of source
    out_source = gp.quicksum(flow[(source, j)] for (i, j) in edges if i == source)
    in_source = gp.quicksum(flow[(i, source)] for (i, j) in edges if j == source)
    model.setObjective(out_source - in_source, GRB.MAXIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}