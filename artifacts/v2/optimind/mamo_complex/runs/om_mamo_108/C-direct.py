import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n = 9  # number of nodes
    source = 0
    sink = 8

    # Build capacity dict from params
    cap = {}
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            key = f"cap_{i}_{j}"
            if key in params:
                cap[(i, j)] = params[key]
            # cap_8_all covers outbound from 8 (all zero, no outbound links)
            # edges from 8 simply won't exist in our arc set

    # Define arcs: all (i,j) where i != j, i != sink, and capacity exists
    arcs = [(i, j) for (i, j) in cap if i != sink and cap[(i, j)] > 0]

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
    total_flow = gp.quicksum(flow[i, j] for (i, j) in arcs if j == sink)
    model.setObjective(total_flow, GRB.MAXIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}