import gurobipy as gp
from gurobipy import GRB

def solve(params):
    capacity_matrix_flat = params["capacity_matrix"]
    n = 9
    source = 0
    sink = 8

    # Support both flat (list of 81 ints) and nested (list of 9 lists) formats
    if isinstance(capacity_matrix_flat[0], (list, tuple)):
        cap_matrix = capacity_matrix_flat
    else:
        cap_matrix = [capacity_matrix_flat[i*n:(i+1)*n] for i in range(n)]

    model = gp.Model("max_flow")
    model.setParam("OutputFlag", 0)

    # Flow variables for each directed edge with positive capacity
    flow = {}
    for i in range(n):
        for j in range(n):
            cap = cap_matrix[i][j]
            if i != j and cap > 0:
                flow[(i, j)] = model.addVar(lb=0.0, ub=float(cap), name=f"f_{i}_{j}")

    model.update()

    # Flow conservation constraints for intermediate nodes
    for node in range(n):
        if node == source or node == sink:
            continue
        outflow = gp.quicksum(flow[(i2, j2)] for (i2, j2) in flow if i2 == node)
        inflow = gp.quicksum(flow[(i2, j2)] for (i2, j2) in flow if j2 == node)
        model.addConstr(inflow == outflow, name=f"conserve_{node}")

    # Objective: maximize flow into the sink
    total_flow = gp.quicksum(flow[(i2, j2)] for (i2, j2) in flow if j2 == sink)
    model.setObjective(total_flow, GRB.MAXIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}