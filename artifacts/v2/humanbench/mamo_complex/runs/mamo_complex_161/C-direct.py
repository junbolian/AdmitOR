import gurobipy as gp
from gurobipy import GRB

def solve(params):
    capacity_list = params["capacity"]

    # Define the arc order as specified in the problem
    arcs_order = [
        (0,1),(0,2),(0,3),(0,4),(0,5),(0,6),(0,7),(0,8),
        (1,0),(1,2),(1,3),(1,4),(1,6),(1,7),(1,8),
        (2,0),(2,1),(2,3),(2,4),(2,5),(2,6),(2,7),(2,8),
        (3,0),(3,1),(3,2),(3,4),(3,5),(3,6),(3,7),(3,8),
        (4,0),(4,1),(4,2),(4,3),(4,5),(4,6),(4,7),(4,8),
        (5,0),(5,1),(5,2),(5,3),(5,4),(5,6),(5,7),(5,8),
        (6,0),(6,1),(6,2),(6,3),(6,4),(6,5),(6,7),(6,8),
        (7,0),(7,1),(7,2),(7,3),(7,4),(7,5),(7,6),(7,8),
        (8,0),(8,1),(8,2),(8,3),(8,4),(8,5),(8,6),(8,7),
    ]

    cap = {}
    for idx, arc in enumerate(arcs_order):
        cap[arc] = capacity_list[idx]

    source = 0
    sink = 8
    nodes = list(range(9))

    model = gp.Model("max_flow")
    model.setParam("OutputFlag", 0)

    # Flow variables
    flow = {}
    for arc, c in cap.items():
        flow[arc] = model.addVar(lb=0.0, ub=c, name=f"f_{arc[0]}_{arc[1]}")

    # Objective: maximize flow into sink
    model.setObjective(
        gp.quicksum(flow[arc] for arc in cap if arc[1] == sink) -
        gp.quicksum(flow[arc] for arc in cap if arc[0] == sink),
        GRB.MAXIMIZE
    )

    # Flow conservation for intermediate nodes
    for node in nodes:
        if node == source or node == sink:
            continue
        in_flow = gp.quicksum(flow[arc] for arc in cap if arc[1] == node)
        out_flow = gp.quicksum(flow[arc] for arc in cap if arc[0] == node)
        model.addConstr(in_flow == out_flow, name=f"conservation_{node}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}