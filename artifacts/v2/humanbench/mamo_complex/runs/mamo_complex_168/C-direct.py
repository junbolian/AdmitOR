import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n = 8
    source = 0
    sink = 7

    # Build capacity dict from params
    cap = {}
    for i in range(n):
        for j in range(n):
            if i != j:
                key = f"capacity_{i}_{j}"
                if key in params:
                    cap[(i, j)] = params[key]
                else:
                    cap[(i, j)] = 0.0

    edges = [(i, j) for i in range(n) for j in range(n) if i != j and cap.get((i, j), 0) > 0]

    model = gp.Model("max_flow")
    model.setParam("OutputFlag", 0)

    flow = model.addVars(edges, lb=0.0, name="flow")

    # Capacity constraints
    for (i, j) in edges:
        model.addConstr(flow[i, j] <= cap[(i, j)], name=f"cap_{i}_{j}")

    # Flow conservation for intermediate nodes
    for node in range(n):
        if node == source or node == sink:
            continue
        in_flow = gp.quicksum(flow[i, j] for (i, j) in edges if j == node)
        out_flow = gp.quicksum(flow[i, j] for (i, j) in edges if i == node)
        model.addConstr(in_flow == out_flow, name=f"conservation_{node}")

    # Objective: maximize flow out of source
    total_flow = gp.quicksum(flow[source, j] for (i, j) in edges if i == source)
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