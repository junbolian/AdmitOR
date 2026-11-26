import gurobipy as gp
from gurobipy import GRB

def solve(params):
    edges = [
        (0, 1), (0, 2), (0, 3), (0, 4), (0, 5),
        (1, 0), (1, 2), (1, 3), (1, 5),
        (2, 0), (2, 1), (2, 3), (2, 4), (2, 5),
        (3, 0), (3, 1), (3, 2), (3, 5),
        (4, 0), (4, 1), (4, 2), (4, 3), (4, 5),
        (5, 0), (5, 1), (5, 2), (5, 3), (5, 4),
    ]

    capacity = {(i, j): params[f"capacity_{i}_{j}"] for (i, j) in edges}

    nodes = list(range(6))
    source = 0
    sink = 5

    model = gp.Model("max_flow")
    model.setParam("OutputFlag", 0)

    flow = model.addVars(edges, lb=0.0, name="flow")

    for (i, j) in edges:
        model.addConstr(flow[i, j] <= capacity[i, j], name=f"cap_{i}_{j}")

    for node in nodes:
        if node == source or node == sink:
            continue
        in_flow = gp.quicksum(flow[i, j] for (i, j) in edges if j == node)
        out_flow = gp.quicksum(flow[i, j] for (i, j) in edges if i == node)
        model.addConstr(in_flow == out_flow, name=f"conservation_{node}")

    # Net flow out of the source
    total_flow = (
        gp.quicksum(flow[i, j] for (i, j) in edges if i == source)
        - gp.quicksum(flow[i, j] for (i, j) in edges if j == source)
    )
    model.setObjective(total_flow, GRB.MAXIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}