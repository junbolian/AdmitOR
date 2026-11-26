import gurobipy as gp
from gurobipy import GRB

def solve(params):
    capacities_flat = params["capacities"]
    n = params["num_stations"]

    # Reconstruct capacity matrix: ordered pairs i != j, row-major
    cap = {}
    idx = 0
    for i in range(n):
        for j in range(n):
            if i != j:
                cap[(i, j)] = capacities_flat[idx]
                idx += 1

    source = 0
    sink = n - 1  # Station 8

    # Build list of arcs with positive capacity
    arcs = [(i, j) for (i, j), c in cap.items() if c > 0]

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

    # Objective: maximize flow out of source
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