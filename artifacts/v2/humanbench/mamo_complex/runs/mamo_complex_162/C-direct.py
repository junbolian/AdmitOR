import gurobipy as gp
from gurobipy import GRB

def solve(params):
    capacity = {}
    n = params["num_cities"]
    
    # Build capacity dict from params
    for i in range(n):
        for j in range(n):
            if i != j:
                key = f"capacity_{i}_{j}"
                if key in params:
                    capacity[(i, j)] = params[key]

    source = 0
    sink = n - 1  # City 5

    # Only arcs with capacity > 0 (but we include all defined arcs; capacity=0 means no flow possible)
    arcs = [(i, j) for (i, j), c in capacity.items()]

    model = gp.Model("max_flow")
    model.setParam("OutputFlag", 0)

    # Flow variables
    flow = model.addVars(arcs, lb=0.0, name="flow")

    # Capacity constraints
    for (i, j) in arcs:
        model.addConstr(flow[i, j] <= capacity[(i, j)], name=f"cap_{i}_{j}")

    # Flow conservation for intermediate nodes
    for node in range(n):
        if node == source or node == sink:
            continue
        inflow = gp.quicksum(flow[i, j] for (i, j) in arcs if j == node)
        outflow = gp.quicksum(flow[i, j] for (i, j) in arcs if i == node)
        model.addConstr(inflow == outflow, name=f"conserve_{node}")

    # Objective: maximize flow out of source
    obj = gp.quicksum(flow[source, j] for (i, j) in arcs if i == source) \
        - gp.quicksum(flow[j, source] for (j, i) in arcs if i == source)
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