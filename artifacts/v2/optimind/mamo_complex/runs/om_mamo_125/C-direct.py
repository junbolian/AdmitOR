import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cap_raw = params["cap"]
    n_nodes = params["n_nodes"]
    source = params["source"]
    sink = params["sink"]

    # Normalize cap to a dict keyed by (i,j) regardless of input format
    if isinstance(cap_raw, dict):
        cap = cap_raw
    else:
        # Assume it's a 2D list/matrix
        cap = {}
        for i in range(len(cap_raw)):
            for j in range(len(cap_raw[i])):
                cap[(i, j)] = cap_raw[i][j]

    nodes = range(n_nodes)
    arcs = [(i, j) for i in nodes for j in nodes if cap.get((i, j), 0) > 0]

    model = gp.Model("max_flow")
    model.setParam("OutputFlag", 0)

    flow = model.addVars(arcs, lb=0.0, name="flow")

    for (i, j) in arcs:
        model.addConstr(flow[i, j] <= cap[(i, j)], name=f"cap_{i}_{j}")

    for node in nodes:
        if node == source or node == sink:
            continue
        in_flow = gp.quicksum(flow[i, j] for (i, j) in arcs if j == node)
        out_flow = gp.quicksum(flow[i, j] for (i, j) in arcs if i == node)
        model.addConstr(in_flow == out_flow, name=f"conservation_{node}")

    total_flow = gp.quicksum(flow[i, j] for (i, j) in arcs if i == source)
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