import gurobipy as gp
from gurobipy import GRB

def solve(params):
    # Nodes: 0 through 8
    # Source: 0, Sink: 8
    # Edges: all (i,j) where i != j, except (8, 7) which doesn't exist per params
    # Build edge list from params
    
    num_nodes = 9
    edges = []
    for i in range(num_nodes):
        for j in range(num_nodes):
            if i != j:
                key = f"capacity_{i}_{j}"
                if key in params:
                    edges.append((i, j))

    capacity = {}
    for (i, j) in edges:
        capacity[(i, j)] = params[f"capacity_{i}_{j}"]

    source = 0
    sink = 8

    model = gp.Model("max_flow")
    model.setParam("OutputFlag", 0)

    # Flow variables
    flow = {}
    for (i, j) in edges:
        flow[(i, j)] = model.addVar(lb=0.0, ub=capacity[(i, j)], name=f"flow_{i}_{j}")

    model.update()

    # Objective: maximize flow into sink
    model.setObjective(
        gp.quicksum(flow[(i, sink)] for (i, j) in edges if j == sink),
        GRB.MAXIMIZE
    )

    # Flow conservation for intermediate nodes
    for node in range(num_nodes):
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
    else:
        return {"objective": None, "status": f"status_{model.Status}"}