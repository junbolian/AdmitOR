import gurobipy as gp
from gurobipy import GRB

def solve(params):
    n_stations = 9
    stations = range(n_stations)
    source = 0
    sink = 8

    # Build capacity dict from params
    capacity = {}
    for i in stations:
        for j in stations:
            if i != j:
                key = f"capacity_{i}_to_{j}"
                capacity[(i, j)] = params[key]

    arcs = [(i, j) for i in stations for j in stations if i != j]

    model = gp.Model("max_flow")
    model.setParam("OutputFlag", 0)

    # Flow variables
    flow = model.addVars(arcs, lb=0.0, name="flow")

    # Capacity constraints
    for (i, j) in arcs:
        model.addConstr(flow[i, j] <= capacity[(i, j)], name=f"cap_{i}_{j}")

    # Flow conservation for intermediate nodes
    for node in stations:
        if node == source or node == sink:
            continue
        model.addConstr(
            gp.quicksum(flow[i, node] for i in stations if i != node) ==
            gp.quicksum(flow[node, j] for j in stations if j != node),
            name=f"conservation_{node}"
        )

    # Objective: maximize flow into sink
    model.setObjective(
        gp.quicksum(flow[i, sink] for i in stations if i != sink) -
        gp.quicksum(flow[sink, j] for j in stations if j != sink),
        GRB.MAXIMIZE
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}