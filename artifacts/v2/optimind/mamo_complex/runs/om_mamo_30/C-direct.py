import gurobipy as gp
from gurobipy import GRB

def solve(params):
    # Define the network edges and read capacities from params
    edges = [
        (0, 1), (0, 2), (0, 3), (0, 5), (0, 6), (0, 7),
        (1, 0), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6),
        (2, 0), (2, 1), (2, 3), (2, 4), (2, 5), (2, 6), (2, 7),
        (3, 0), (3, 1), (3, 2), (3, 4), (3, 5), (3, 7),
        (4, 0), (4, 1), (4, 2), (4, 3), (4, 5), (4, 6), (4, 7),
        (5, 0), (5, 1), (5, 2), (5, 3), (5, 4), (5, 6), (5, 7),
        (6, 0), (6, 1), (6, 2), (6, 3), (6, 4), (6, 5), (6, 7),
        (7, 0), (7, 1), (7, 3), (7, 4), (7, 5), (7, 6),
    ]

    capacity = {}
    for (i, j) in edges:
        key = f"capacity_{i}_{j}"
        capacity[(i, j)] = params[key]

    source = 0
    sink = 7
    nodes = list(range(8))

    model = gp.Model("max_flow")
    model.setParam("OutputFlag", 0)

    # Flow variables
    flow = {}
    for (i, j) in edges:
        flow[(i, j)] = model.addVar(lb=0.0, ub=capacity[(i, j)], name=f"flow_{i}_{j}")

    # Objective: maximize flow out of source
    model.setObjective(
        gp.quicksum(flow[(source, j)] for (i, j) in edges if i == source)
        - gp.quicksum(flow[(j, source)] for (j, i) in edges if i == source),
        GRB.MAXIMIZE
    )

    # Flow conservation for intermediate nodes
    for node in nodes:
        if node == source or node == sink:
            continue
        inflow = gp.quicksum(flow[(i, j)] for (i, j) in edges if j == node)
        outflow = gp.quicksum(flow[(i, j)] for (i, j) in edges if i == node)
        model.addConstr(inflow == outflow, name=f"conservation_{node}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}