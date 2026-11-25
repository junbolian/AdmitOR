import gurobipy as gp
from gurobipy import GRB

def solve(params):
    # Define the network edges (i, j) and their param key suffixes
    edges = [
        (0, 1), (0, 2), (0, 5),
        (1, 0), (1, 2),
        (2, 0), (2, 1), (2, 3),
        (3, 2), (3, 4),
        (4, 1), (4, 2), (4, 3), (4, 5),
        (5, 0), (5, 3), (5, 4),
    ]

    nodes = range(6)

    # Read parameters from dict
    cap = {(i, j): params[f"cap_{i}_{j}"] for (i, j) in edges}
    cost = {(i, j): params[f"cost_{i}_{j}"] for (i, j) in edges}

    # Minimum flows: only defined for specific pipes; default 0
    min_flow_keys = [
        (0, 1), (1, 0), (1, 2), (2, 1), (2, 3), (3, 4), (4, 1)
    ]
    min_flow = {}
    for (i, j) in edges:
        if (i, j) in min_flow_keys:
            min_flow[(i, j)] = params[f"min_flow_{i}_{j}"]
        else:
            min_flow[(i, j)] = 0.0

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Flow variables
    flow = {}
    for (i, j) in edges:
        flow[(i, j)] = model.addVar(
            lb=min_flow[(i, j)],
            ub=cap[(i, j)],
            name=f"flow_{i}_{j}"
        )

    model.update()

    # Flow conservation at each node: inflow == outflow
    for node in nodes:
        inflow = gp.quicksum(flow[(i, j)] for (i, j) in edges if j == node)
        outflow = gp.quicksum(flow[(i, j)] for (i, j) in edges if i == node)
        model.addConstr(inflow == outflow, name=f"balance_{node}")

    # Objective: minimize total pumping energy cost
    model.setObjective(
        gp.quicksum(cost[(i, j)] * flow[(i, j)] for (i, j) in edges),
        GRB.MINIMIZE
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"gurobi_status_{model.Status}"}