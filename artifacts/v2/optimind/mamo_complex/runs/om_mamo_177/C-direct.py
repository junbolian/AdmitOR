import gurobipy as gp
from gurobipy import GRB

def solve(params):
    arc_capacities = params["arc_capacities"]
    
    n = 8  # number of nodes
    source = 0
    sink = 7

    def get_cap(i, j):
        # Support dict with tuple keys, list of lists, or flat list
        if isinstance(arc_capacities, dict):
            return arc_capacities.get((i, j), 0)
        elif isinstance(arc_capacities, (list, tuple)):
            first = arc_capacities[0]
            if isinstance(first, (list, tuple)):
                return first[j] if j < len(first) else 0
            else:
                # flat list of length n*n
                return arc_capacities[i * n + j]
        else:
            return arc_capacities[i][j]

    # Re-implement get_cap properly for list of lists
    def capacity(i, j):
        if isinstance(arc_capacities, dict):
            return arc_capacities.get((i, j), 0)
        try:
            val = arc_capacities[i][j]
            return val
        except (TypeError, KeyError, IndexError):
            pass
        try:
            return arc_capacities[i * n + j]
        except (TypeError, KeyError, IndexError):
            return 0

    model = gp.Model("max_flow")
    model.setParam("OutputFlag", 0)

    # Create flow variables for each arc with positive capacity
    flow = {}
    for i in range(n):
        for j in range(n):
            cap = capacity(i, j)
            if cap > 0:
                flow[i, j] = model.addVar(lb=0.0, ub=float(cap), name=f"flow_{i}_{j}")

    model.update()

    # Flow conservation for intermediate nodes
    for node in range(n):
        if node == source or node == sink:
            continue
        outflow = gp.quicksum(flow[i, j] for (i, j) in flow if i == node)
        inflow = gp.quicksum(flow[i, j] for (i, j) in flow if j == node)
        model.addConstr(outflow == inflow, name=f"conservation_{node}")

    # Maximize net flow out of source
    out_source = gp.quicksum(flow[source, j] for (i, j) in flow if i == source)
    in_source = gp.quicksum(flow[i, source] for (i, j) in flow if j == source)
    total_flow = out_source - in_source

    model.setObjective(total_flow, GRB.MAXIMIZE)
    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}