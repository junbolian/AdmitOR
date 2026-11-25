import gurobipy as gp
from gurobipy import GRB

def solve(params):
    # Define arcs and read params
    arcs = [
        (0, 1), (0, 6), (0, 8),
        (1, 2),
        (2, 3), (2, 7),
        (3, 4),
        (4, 5), (4, 7), (4, 8),
        (5, 6),
        (6, 7), (6, 8),
        (7, 8),
        (8, 9),
    ]

    capacity = {}
    cost = {}
    for (i, j) in arcs:
        capacity[(i, j)] = params[f"capacity_{i}_{j}"]
        cost[(i, j)] = params[f"cost_{i}_{j}"]

    # Nodes
    nodes = list(range(10))
    source = 0
    sink = 9

    # --- Phase 1: maximize flow ---
    model = gp.Model()
    model.setParam("OutputFlag", 0)

    flow = model.addVars(arcs, lb=0.0, name="flow")

    # Capacity constraints
    for (i, j) in arcs:
        model.addConstr(flow[i, j] <= capacity[(i, j)], name=f"cap_{i}_{j}")

    # Flow conservation for intermediate nodes
    for nd in nodes:
        if nd == source or nd == sink:
            continue
        in_flow = gp.quicksum(flow[i, j] for (i, j) in arcs if j == nd)
        out_flow = gp.quicksum(flow[i, j] for (i, j) in arcs if i == nd)
        model.addConstr(in_flow == out_flow, name=f"conserve_{nd}")

    # Net outflow from source = total flow
    total_flow = model.addVar(lb=0.0, name="total_flow")
    source_out = gp.quicksum(flow[i, j] for (i, j) in arcs if i == source)
    source_in  = gp.quicksum(flow[i, j] for (i, j) in arcs if j == source)
    model.addConstr(total_flow == source_out - source_in, name="def_total_flow")

    model.setObjective(total_flow, GRB.MAXIMIZE)
    model.optimize()

    if model.Status not in (GRB.OPTIMAL, GRB.SUBOPTIMAL):
        return {"objective": None, "status": "infeasible_phase1"}

    max_flow_val = model.ObjVal

    # --- Phase 2: minimize cost subject to achieving max flow ---
    model2 = gp.Model()
    model2.setParam("OutputFlag", 0)

    flow2 = model2.addVars(arcs, lb=0.0, name="flow2")

    for (i, j) in arcs:
        model2.addConstr(flow2[i, j] <= capacity[(i, j)], name=f"cap_{i}_{j}")

    for nd in nodes:
        if nd == source or nd == sink:
            continue
        in_flow2  = gp.quicksum(flow2[i, j] for (i, j) in arcs if j == nd)
        out_flow2 = gp.quicksum(flow2[i, j] for (i, j) in arcs if i == nd)
        model2.addConstr(in_flow2 == out_flow2, name=f"conserve_{nd}")

    source_out2 = gp.quicksum(flow2[i, j] for (i, j) in arcs if i == source)
    source_in2  = gp.quicksum(flow2[i, j] for (i, j) in arcs if j == source)
    model2.addConstr(source_out2 - source_in2 == max_flow_val, name="fix_flow")

    total_cost = gp.quicksum(cost[(i, j)] * flow2[i, j] for (i, j) in arcs)
    model2.setObjective(total_cost, GRB.MINIMIZE)
    model2.optimize()

    if model2.Status not in (GRB.OPTIMAL, GRB.SUBOPTIMAL):
        return {"objective": None, "status": "infeasible_phase2"}

    # Objective encodes lexicographic result: primary = max flow, secondary = min cost
    # Return combined objective as (max_flow, min_cost) represented numerically
    # Per problem convention return the min cost as the reported objective
    # (flow is maximized as the primary criterion)
    return {"objective": model2.ObjVal, "status": "optimal"}