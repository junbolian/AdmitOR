import gurobipy as gp
from gurobipy import GRB

def solve(params):
    capacity_matrix = params["capacity_matrix"]
    n = 9
    source = 0
    sink = 8

    model = gp.Model("max_flow")
    model.setParam("OutputFlag", 0)

    # Build flow variables for each (i, j) where capacity > 0 and i != j
    flow = {}
    for i in range(n):
        for j in range(n):
            if i != j:
                cap = capacity_matrix[i * n + j]
                if cap > 0:
                    flow[(i, j)] = model.addVar(lb=0.0, ub=cap, name=f"f_{i}_{j}")

    model.update()

    # Flow conservation for intermediate nodes
    for node in range(n):
        if node == source or node == sink:
            continue
        in_flow = gp.quicksum(flow[(i, node)] for i in range(n) if (i, node) in flow)
        out_flow = gp.quicksum(flow[(node, j)] for j in range(n) if (node, j) in flow)
        model.addConstr(in_flow == out_flow, name=f"balance_{node}")

    # Objective: maximize flow out of source
    total_out = gp.quicksum(flow[(source, j)] for j in range(n) if (source, j) in flow)
    total_in = gp.quicksum(flow[(i, source)] for i in range(n) if (i, source) in flow)
    net_flow = total_out - total_in

    model.setObjective(net_flow, GRB.MAXIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}