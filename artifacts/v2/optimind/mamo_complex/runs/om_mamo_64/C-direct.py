import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n = 8
    source = 0
    sink = 7

    # Build capacity dict from params
    capacity = {}
    for i in range(n):
        for j in range(n):
            if i != j:
                key = f"capacity_{i}_{j}"
                if key in params:
                    capacity[(i, j)] = params[key]
                else:
                    capacity[(i, j)] = 0.0

    edges = [(i, j) for i in range(n) for j in range(n) if i != j]

    model = gp.Model("max_flow")
    model.setParam("OutputFlag", 0)

    # Flow variables
    flow = model.addVars(edges, lb=0.0, name="flow")

    # Capacity constraints
    for (i, j) in edges:
        model.addConstr(flow[i, j] <= capacity[(i, j)], name=f"cap_{i}_{j}")

    # Flow conservation for intermediate nodes
    for node in range(n):
        if node == source or node == sink:
            continue
        model.addConstr(
            gp.quicksum(flow[i, node] for i in range(n) if i != node) ==
            gp.quicksum(flow[node, j] for j in range(n) if j != node),
            name=f"conservation_{node}"
        )

    # Objective: maximize flow into sink
    obj = gp.quicksum(flow[i, sink] for i in range(n) if i != sink)
    model.setObjective(obj, GRB.MAXIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}