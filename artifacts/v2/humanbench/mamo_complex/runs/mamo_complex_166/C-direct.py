import gurobipy as gp
from gurobipy import GRB

def solve(params):
    # Define all directed edges with their capacities from params
    edges = [
        (0, 1), (0, 2), (0, 3), (0, 5), (0, 6),
        (1, 0), (1, 2), (1, 3), (1, 5),
        (2, 0), (2, 1), (2, 3), (2, 4), (2, 6),
        (3, 0), (3, 1), (3, 2), (3, 4), (3, 5), (3, 6),
        (4, 0), (4, 1), (4, 2), (4, 3), (4, 5), (4, 6),
        (5, 0), (5, 1), (5, 2), (5, 3), (5, 4), (5, 6),
        (6, 0), (6, 1), (6, 2), (6, 3), (6, 4), (6, 5),
    ]

    capacity = {(i, j): params[f"capacity_{i}_{j}"] for (i, j) in edges}

    nodes = list(range(7))
    source = 0
    sink = 6

    model = gp.Model("max_flow")
    model.setParam("OutputFlag", 0)

    # Flow variables for each edge
    flow = model.addVars(edges, lb=0.0, name="flow")

    # Capacity constraints
    for (i, j) in edges:
        model.addConstr(flow[i, j] <= capacity[i, j], name=f"cap_{i}_{j}")

    # Flow conservation for intermediate nodes
    for node in nodes:
        if node == source or node == sink:
            continue
        inflow = gp.quicksum(flow[i, j] for (i, j) in edges if j == node)
        outflow = gp.quicksum(flow[i, j] for (i, j) in edges if i == node)
        model.addConstr(inflow == outflow, name=f"conserve_{node}")

    # Objective: maximize flow into sink
    total_flow = gp.quicksum(flow[i, j] for (i, j) in edges if j == sink) - \
                 gp.quicksum(flow[i, j] for (i, j) in edges if i == sink)
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