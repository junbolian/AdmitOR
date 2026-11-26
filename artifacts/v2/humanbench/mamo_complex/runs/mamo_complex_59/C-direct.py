import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n = 9
    nodes = range(n)
    source = 0
    sink = 8

    # Build capacity dict from params
    cap = {}
    for i in nodes:
        for j in nodes:
            if i != j:
                key = f"capacity_{i}_{j}"
                if key in params:
                    cap[(i, j)] = params[key]

    edges = list(cap.keys())

    model = gp.Model("max_flow")
    model.setParam("OutputFlag", 0)

    # Flow variables
    flow = model.addVars(edges, lb=0.0, name="flow")

    # Capacity constraints
    for (i, j) in edges:
        model.addConstr(flow[(i, j)] <= cap[(i, j)], name=f"cap_{i}_{j}")

    # Flow conservation for intermediate nodes
    for node in nodes:
        if node == source or node == sink:
            continue
        inflow = gp.quicksum(flow[(i, node)] for (i, j) in edges if j == node)
        outflow = gp.quicksum(flow[(node, j)] for (i, j) in edges if i == node)
        model.addConstr(inflow == outflow, name=f"conserve_{node}")

    # Objective: maximize flow into sink
    total_flow = gp.quicksum(flow[(i, sink)] for (i, j) in edges if j == sink)
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