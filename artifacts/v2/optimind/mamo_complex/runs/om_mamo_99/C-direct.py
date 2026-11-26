import gurobipy as gp
from gurobipy import GRB

def solve(params):
    # Build capacity dict from params
    edges = [
        (0, 1), (0, 2), (0, 3), (0, 4), (0, 5),
        (1, 0), (1, 2), (1, 4), (1, 5),
        (2, 0), (2, 1), (2, 3), (2, 4), (2, 5),
        (3, 0), (3, 1), (3, 2), (3, 4), (3, 5),
        (4, 0), (4, 1), (4, 2), (4, 3), (4, 5),
        (5, 0), (5, 1), (5, 2), (5, 3), (5, 4),
    ]

    capacity = {(i, j): params[f"capacity_{i}_{j}"] for (i, j) in edges}

    source = 0
    sink = 5
    nodes = list(range(6))

    model = gp.Model("max_flow")
    model.setParam("OutputFlag", 0)

    # Flow variables for each edge
    flow = {}
    for (i, j) in edges:
        flow[(i, j)] = model.addVar(lb=0.0, ub=capacity[(i, j)], name=f"flow_{i}_{j}")

    model.update()

    # Flow conservation constraints for intermediate nodes
    for node in nodes:
        if node == source or node == sink:
            continue
        in_flow = gp.quicksum(flow[(i, j)] for (i, j) in edges if j == node)
        out_flow = gp.quicksum(flow[(i, j)] for (i, j) in edges if i == node)
        model.addConstr(in_flow == out_flow, name=f"conservation_{node}")

    # Objective: maximize flow out of source
    total_flow = gp.quicksum(flow[(i, j)] for (i, j) in edges if i == source)
    model.setObjective(total_flow, GRB.MAXIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}