import gurobipy as gp
from gurobipy import GRB

def solve(params):
    edge_capacities = params["edge_capacities"]
    num_cities = params["num_cities"]

    # Reconstruct the exact edge list in the order described in the problem text.
    # Each row lists the destinations explicitly (skipping self and some nodes).
    # City 0 -> 1,2,3,4,5,6,7,8  (8 edges)
    # City 1 -> 0,2,4,5,6,7,8    (7 edges, skip 3)
    # City 2 -> 0,1,4,5,6,7,8    (7 edges, skip 3)
    # City 3 -> 0,1,2,4,5,6,7,8  (8 edges, skip none except self)
    # City 4 -> 0,1,2,3,5,6,7,8  (8 edges, skip none except self)
    # City 5 -> 0,1,2,3,4,6,7,8  (8 edges, skip none except self)
    # City 6 -> 0,1,2,3,4,5,7,8  (8 edges, skip none except self)
    # City 7 -> 0,1,2,3,4,5,6,8  (8 edges, skip none except self)
    # City 8 -> 0,1,2,3,4,5,6,7  (8 edges, skip none except self)

    edge_list = []
    # City 0 outgoing
    for j in range(1, 9):
        edge_list.append((0, j))
    # City 1 outgoing: 0,2,4,5,6,7,8 (no 3)
    for j in [0, 2, 4, 5, 6, 7, 8]:
        edge_list.append((1, j))
    # City 2 outgoing: 0,1,4,5,6,7,8 (no 3)
    for j in [0, 1, 4, 5, 6, 7, 8]:
        edge_list.append((2, j))
    # City 3 outgoing: 0,1,2,4,5,6,7,8 (no 3)
    for j in [0, 1, 2, 4, 5, 6, 7, 8]:
        edge_list.append((3, j))
    # City 4 outgoing: 0,1,2,3,5,6,7,8 (no 4)
    for j in [0, 1, 2, 3, 5, 6, 7, 8]:
        edge_list.append((4, j))
    # City 5 outgoing: 0,1,2,3,4,6,7,8 (no 5)
    for j in [0, 1, 2, 3, 4, 6, 7, 8]:
        edge_list.append((5, j))
    # City 6 outgoing: 0,1,2,3,4,5,7,8 (no 6)
    for j in [0, 1, 2, 3, 4, 5, 7, 8]:
        edge_list.append((6, j))
    # City 7 outgoing: 0,1,2,3,4,5,6,8 (no 7)
    for j in [0, 1, 2, 3, 4, 5, 6, 8]:
        edge_list.append((7, j))
    # City 8 outgoing: 0,1,2,3,4,5,6,7 (no 8)
    for j in [0, 1, 2, 3, 4, 5, 6, 7]:
        edge_list.append((8, j))

    if len(edge_list) != len(edge_capacities):
        return {"objective": None, "status": f"edge count mismatch: expected {len(edge_list)}, got {len(edge_capacities)}"}

    cap = {}
    for idx, (i, j) in enumerate(edge_list):
        cap[(i, j)] = edge_capacities[idx]

    source = 0
    sink = num_cities - 1  # City 8

    model = gp.Model("max_flow")
    model.setParam("OutputFlag", 0)

    # Flow variables for each directed edge with positive capacity
    flow = {}
    for (i, j), c in cap.items():
        if c > 0:
            flow[(i, j)] = model.addVar(lb=0.0, ub=float(c), name=f"f_{i}_{j}")

    model.update()

    # Flow conservation for intermediate nodes
    for node in range(num_cities):
        if node == source or node == sink:
            continue
        outflow = gp.quicksum(flow[(i, j)] for (i, j) in flow if i == node)
        inflow = gp.quicksum(flow[(i, j)] for (i, j) in flow if j == node)
        model.addConstr(outflow == inflow, name=f"conservation_{node}")

    # Objective: maximize total flow into sink
    total_flow = gp.quicksum(flow[(i, j)] for (i, j) in flow if j == sink)
    model.setObjective(total_flow, GRB.MAXIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}