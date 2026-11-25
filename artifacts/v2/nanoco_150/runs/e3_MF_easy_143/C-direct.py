import gurobipy as gp
from gurobipy import GRB

def solve(params):
    capacity = params["capacity"]
    cost = params["cost"]

    # Edges in order: (0-1,0-2,0-3,0-7,1-2,1-5,2-3,2-5,2-6,3-4,3-5,4-5,4-6,4-7,5-6,5-7,6-7)
    edges = [
        (0, 1), (0, 2), (0, 3), (0, 7),
        (1, 2), (1, 5),
        (2, 3), (2, 5), (2, 6),
        (3, 4), (3, 5),
        (4, 5), (4, 6), (4, 7),
        (5, 6), (5, 7),
        (6, 7)
    ]

    num_edges = len(edges)
    source = 0
    sink = 7
    intermediate_nodes = list(range(1, 7))

    model = gp.Model("max_flow")
    model.setParam("OutputFlag", 0)

    # Flow variables
    flow = model.addVars(num_edges, lb=0.0, name="flow")

    # Capacity constraints
    for i in range(num_edges):
        model.addConstr(flow[i] <= capacity[i], name=f"cap_{i}")

    # Flow conservation for intermediate nodes
    for node in intermediate_nodes:
        inflow = gp.quicksum(
            flow[i] for i, (u, v) in enumerate(edges) if v == node
        )
        outflow = gp.quicksum(
            flow[i] for i, (u, v) in enumerate(edges) if u == node
        )
        model.addConstr(inflow == outflow, name=f"conservation_{node}")

    # Objective: maximize total flow out of source
    total_flow = gp.quicksum(
        flow[i] for i, (u, v) in enumerate(edges) if u == source
    )
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