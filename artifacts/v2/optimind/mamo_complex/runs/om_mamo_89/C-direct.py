import gurobipy as gp
from gurobipy import GRB

def solve(params):
    # Build capacity dict from params
    nodes = list(range(7))
    # All directed edges (i->j where i != j)
    edges = [(i, j) for i in nodes for j in nodes if i != j]

    # Map edge to capacity from params
    cap = {}
    for (i, j) in edges:
        key = f"c{i}{j}"
        cap[(i, j)] = params[key]

    model = gp.Model("max_flow")
    model.setParam("OutputFlag", 0)

    # Flow variables for each directed edge
    flow = model.addVars(edges, lb=0.0, name="flow")

    # Capacity constraints
    for (i, j) in edges:
        model.addConstr(flow[i, j] <= cap[(i, j)], name=f"cap_{i}_{j}")

    # Flow conservation for intermediate nodes (1, 2, 3, 4, 5)
    source = 0
    sink = 6
    for node in nodes:
        if node == source or node == sink:
            continue
        inflow = gp.quicksum(flow[i, node] for i in nodes if i != node)
        outflow = gp.quicksum(flow[node, j] for j in nodes if j != node)
        model.addConstr(inflow == outflow, name=f"conserve_{node}")

    # Objective: maximize flow into sink
    total_flow = gp.quicksum(flow[i, sink] for i in nodes if i != sink)
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