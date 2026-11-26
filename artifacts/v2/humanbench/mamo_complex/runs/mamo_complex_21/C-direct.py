import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cap_0_1 = params["capacity_0_1"]
    cap_0_2 = params["capacity_0_2"]
    cap_0_3 = params["capacity_0_3"]
    cap_0_4 = params["capacity_0_4"]
    cap_0_5 = params["capacity_0_5"]
    cap_0_6 = params["capacity_0_6"]
    cap_0_7 = params["capacity_0_7"]
    cap_0_8 = params["capacity_0_8"]
    max_from_1 = params["max_capacity_from_1"]
    max_from_2 = params["max_capacity_from_2"]
    cap_7_3   = params["capacity_7_3"]
    max_to_8  = params["max_capacity_to_8"]
    cap_3_8   = params["capacity_3_8"]

    # Build capacity dict: (i, j) -> capacity
    # Nodes: 0..8, source=0, sink=8
    # From node 0: given directly
    # From node 1: up to max_from_1 to each other node (not self, not back to 0 as that would be reverse)
    # From node 2: up to max_from_2 to each other node
    # From node 7: 7->3 given; others from 7 not specified -> 0
    # From node 3: 3->8 given; others from 3 not specified -> 0
    # Into node 8: bounded by max_to_8 (already captured per-link)
    # Node 8 sends nothing (destination)
    # Nodes 4,5,6 send nothing (not described as having outgoing links)

    # Edges: define all possible (i,j) with capacity > 0 or possibly nonzero
    # From 0:
    edges = {}
    edges[(0,1)] = cap_0_1
    edges[(0,2)] = cap_0_2
    edges[(0,3)] = cap_0_3
    edges[(0,4)] = cap_0_4
    edges[(0,5)] = cap_0_5
    edges[(0,6)] = cap_0_6
    edges[(0,7)] = cap_0_7
    edges[(0,8)] = cap_0_8

    # From 1: to nodes 0..8 except 1, up to max_from_1
    # But flow into 8 also bounded by max_to_8; use min
    for j in range(9):
        if j == 1:
            continue
        cap = max_from_1
        if j == 8:
            cap = min(max_from_1, max_to_8)
        edges[(1, j)] = cap

    # From 2: to nodes 0..8 except 2, up to max_from_2
    for j in range(9):
        if j == 2:
            continue
        cap = max_from_2
        if j == 8:
            cap = min(max_from_2, max_to_8)
        edges[(2, j)] = cap

    # From 7: only 7->3 specified
    edges[(7, 3)] = cap_7_3

    # From 3: only 3->8 specified
    edges[(3, 8)] = cap_3_8

    # Remove self-loops just in case
    edges = {(i,j): c for (i,j), c in edges.items() if i != j and c > 0}

    model = gp.Model("maxflow")
    model.setParam("OutputFlag", 0)

    # Flow variables
    flow = {}
    for (i, j), cap in edges.items():
        flow[(i,j)] = model.addVar(lb=0.0, ub=cap, name=f"f_{i}_{j}")

    model.update()

    # Flow conservation for intermediate nodes (1..7)
    for node in range(1, 8):
        in_flow  = gp.quicksum(flow[(i,j)] for (i,j) in edges if j == node)
        out_flow = gp.quicksum(flow[(i,j)] for (i,j) in edges if i == node)
        model.addConstr(in_flow == out_flow, name=f"conservation_{node}")

    # Objective: maximize flow into sink (node 8)
    total_in_8 = gp.quicksum(flow[(i,j)] for (i,j) in edges if j == 8)
    model.setObjective(total_in_8, GRB.MAXIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}