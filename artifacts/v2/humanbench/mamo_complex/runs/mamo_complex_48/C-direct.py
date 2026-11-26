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
    cap_high_1_5 = params["capacity_1_5_high"]
    cap_low    = params["capacity_range_low"]
    cap_high   = params["capacity_range_high"]

    # Build edge list with capacities
    # Edges from node 0
    edges = {
        (0, 1): cap_0_1,
        (0, 2): cap_0_2,
        (0, 3): cap_0_3,
        (0, 4): cap_0_4,
        (0, 5): cap_0_5,
        (0, 6): cap_0_6,
        (0, 7): cap_0_7,
        (0, 8): cap_0_8,
    }

    # Internal edges among nodes 1-8
    # Node 2 -> 1 and 2 -> 5 get high capacity (cap_high_1_5)
    # Others alternate between cap_low and cap_high to reflect the 1-20 TB range
    # Using a structured assignment: edge (i,j) with i<j gets cap_high if (i+j) is even, else cap_low
    # but we must respect: 2->1 and 2->5 = cap_high_1_5
    internal_nodes = list(range(1, 9))
    for i in internal_nodes:
        for j in internal_nodes:
            if i == j:
                continue
            # No back-edges to 0
            if j == 0:
                continue
            if i == 2 and j == 1:
                edges[(i, j)] = cap_high_1_5
            elif i == 2 and j == 5:
                edges[(i, j)] = cap_high_1_5
            else:
                # Assign alternating low/high based on index parity
                if (i + j) % 2 == 0:
                    edges[(i, j)] = cap_high
                else:
                    edges[(i, j)] = cap_low

    source = 0
    sink   = 8

    model = gp.Model("max_flow")
    model.setParam("OutputFlag", 0)

    # Flow variables
    flow = {}
    for (i, j), cap in edges.items():
        flow[(i, j)] = model.addVar(lb=0.0, ub=cap, name=f"f_{i}_{j}")

    model.update()

    # Flow conservation for intermediate nodes (not source, not sink)
    for node in range(9):
        if node == source or node == sink:
            continue
        in_flow  = gp.quicksum(flow[(i, j)] for (i, j) in edges if j == node)
        out_flow = gp.quicksum(flow[(i, j)] for (i, j) in edges if i == node)
        model.addConstr(in_flow == out_flow, name=f"conservation_{node}")

    # Objective: maximize flow into sink
    obj = gp.quicksum(flow[(i, j)] for (i, j) in edges if j == sink)
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