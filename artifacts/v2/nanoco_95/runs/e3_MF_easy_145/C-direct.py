import gurobipy as gp
from gurobipy import GRB

def solve(params):
    capacities = params["capacities"]
    unit_costs = params["unit_costs"]
    # node_coords is informational only

    # Fixed graph structure: 14 directed channels (0-indexed)
    edges = [
        (0, 1), (0, 2), (0, 6), (0, 8),
        (1, 2), (1, 5),
        (2, 3), (2, 6),
        (3, 4),
        (4, 5),
        (5, 6),
        (6, 7), (6, 8),
        (7, 8),
    ]
    num_edges = 14
    source = 0
    sink = 8
    intermediate_nodes = list(range(1, 8))  # nodes 1-7

    model = gp.Model("interbank_max_flow")
    model.setParam("OutputFlag", 0)

    # Decision variables: flow on each channel
    flow = model.addVars(num_edges, lb=0.0, name="flow")

    # Capacity constraints
    for i in range(num_edges):
        model.addConstr(flow[i] <= capacities[i], name=f"cap_{i}")

    # Flow conservation for intermediate nodes 1-7
    for node in intermediate_nodes:
        inflow = gp.quicksum(flow[i] for i, (u, v) in enumerate(edges) if v == node)
        outflow = gp.quicksum(flow[i] for i, (u, v) in enumerate(edges) if u == node)
        model.addConstr(inflow == outflow, name=f"conserve_{node}")

    # Objective: maximize total flow into sink (node 8)
    total_flow = gp.quicksum(flow[i] for i, (u, v) in enumerate(edges) if v == sink)
    model.setObjective(total_flow, GRB.MAXIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"gurobi_status_{model.Status}"}