import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n_nodes = 8
    source = 0
    sink = 7

    # Build edge list and capacity dict from params
    edges = []
    capacity = {}
    for i in range(n_nodes):
        for j in range(n_nodes):
            if i != j:
                key = f"capacity_{i}_{j}"
                if key in params:
                    cap = params[key]
                    edges.append((i, j))
                    capacity[(i, j)] = cap

    model = gp.Model("max_flow")
    model.setParam("OutputFlag", 0)

    # Flow variables
    flow = model.addVars(edges, lb=0.0, name="flow")

    # Capacity constraints
    for (i, j) in edges:
        model.addConstr(flow[i, j] <= capacity[(i, j)], name=f"cap_{i}_{j}")

    # Flow conservation for intermediate nodes
    for node in range(n_nodes):
        if node == source or node == sink:
            continue
        inflow = gp.quicksum(flow[i, j] for (i, j) in edges if j == node)
        outflow = gp.quicksum(flow[i, j] for (i, j) in edges if i == node)
        model.addConstr(inflow == outflow, name=f"conserve_{node}")

    # Objective: maximize flow out of source
    total_flow = gp.quicksum(flow[source, j] for (i, j) in edges if i == source)
    # Subtract any flow coming back into source
    back_to_source = gp.quicksum(flow[i, source] for (i, j) in edges if j == source)
    model.setObjective(total_flow - back_to_source, GRB.MAXIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}