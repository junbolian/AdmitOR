import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n = 6
    source = 0
    sink = 5

    # Build capacity dict from params
    arcs = []
    cap = {}
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            key = f"capacity_{i}_{j}"
            if key in params:
                c = params[key]
                if c > 0:
                    arcs.append((i, j))
                    cap[(i, j)] = c

    model = gp.Model("max_flow")
    model.setParam("OutputFlag", 0)

    # Flow variables
    flow = model.addVars(arcs, lb=0.0, name="flow")

    # Capacity constraints
    for (i, j) in arcs:
        model.addConstr(flow[i, j] <= cap[(i, j)], name=f"cap_{i}_{j}")

    # Flow conservation for intermediate nodes
    for node in range(n):
        if node == source or node == sink:
            continue
        in_flow = gp.quicksum(flow[i, j] for (i, j) in arcs if j == node)
        out_flow = gp.quicksum(flow[i, j] for (i, j) in arcs if i == node)
        model.addConstr(in_flow == out_flow, name=f"conservation_{node}")

    # Objective: maximize flow out of source
    obj = gp.quicksum(flow[i, j] for (i, j) in arcs if i == source)
    model.setObjective(obj, GRB.MAXIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}