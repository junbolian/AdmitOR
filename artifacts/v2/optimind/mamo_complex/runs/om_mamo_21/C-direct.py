import gurobipy as gp
from gurobipy import GRB

def solve(params):
    capacity_matrix = params["capacity_matrix"]
    n = len(capacity_matrix)
    source = 0
    sink = n - 1

    # Build arc list from capacity matrix
    arcs = []
    cap = {}
    for i in range(n):
        for j in range(n):
            if capacity_matrix[i][j] > 0:
                arcs.append((i, j))
                cap[(i, j)] = capacity_matrix[i][j]

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
        inflow = gp.quicksum(flow[i, j] for (i, j) in arcs if j == node)
        outflow = gp.quicksum(flow[i, j] for (i, j) in arcs if i == node)
        model.addConstr(inflow == outflow, name=f"conserve_{node}")

    # Objective: maximize flow into sink
    total_flow = gp.quicksum(flow[i, j] for (i, j) in arcs if j == sink) - \
                 gp.quicksum(flow[i, j] for (i, j) in arcs if i == sink)
    model.setObjective(total_flow, GRB.MAXIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}