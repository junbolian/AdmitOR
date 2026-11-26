import gurobipy as gp
from gurobipy import GRB

def solve(params):
    line_capacities_raw = params["line_capacities"]

    # Normalize keys: handle both (i,j) tuples and other formats
    line_capacities = {}
    for key, cap in line_capacities_raw.items():
        # key could be a tuple, list, or string representation
        if isinstance(key, (list, tuple)):
            i, j = int(key[0]), int(key[1])
        else:
            # Try parsing as string like "(0, 1)" or "0,1"
            key_str = str(key).strip().strip("()")
            parts = key_str.split(",")
            i, j = int(parts[0].strip()), int(parts[1].strip())
        line_capacities[(i, j)] = cap

    # Determine the set of nodes from the keys
    nodes = set()
    for (i, j) in line_capacities:
        nodes.add(i)
        nodes.add(j)
    nodes = sorted(nodes)

    source = 0
    sink = 7

    # Build the set of arcs with positive capacity
    arcs = [(i, j) for (i, j), cap in line_capacities.items() if cap > 0]

    model = gp.Model("max_flow")
    model.setParam("OutputFlag", 0)

    # Flow variables
    flow = model.addVars(arcs, lb=0.0, name="flow")

    # Capacity constraints
    for (i, j) in arcs:
        model.addConstr(flow[i, j] <= line_capacities[(i, j)], name=f"cap_{i}_{j}")

    # Flow conservation for intermediate nodes
    for node in nodes:
        if node == source or node == sink:
            continue
        inflow = gp.quicksum(flow[i, j] for (i, j) in arcs if j == node)
        outflow = gp.quicksum(flow[i, j] for (i, j) in arcs if i == node)
        model.addConstr(inflow == outflow, name=f"conserve_{node}")

    # Objective: maximize net flow out of source
    obj = gp.quicksum(flow[i, j] for (i, j) in arcs if i == source) - \
          gp.quicksum(flow[i, j] for (i, j) in arcs if j == source)
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