import gurobipy as gp
from gurobipy import GRB

def solve(params):
    capacities = params["capacities"]
    unit_costs = params["unit_costs"]
    # node_coords_x and node_coords_y are provided but not used in the LP

    # Arc definitions (fixed topology)
    arcs = [
        (0, 1), (1, 2), (1, 7), (2, 3), (2, 6),
        (3, 4), (3, 8), (3, 9), (4, 5), (4, 8),
        (5, 6), (6, 7), (7, 8), (7, 9), (8, 9)
    ]
    num_arcs = len(arcs)
    arc_index = {arc: i for i, arc in enumerate(arcs)}

    source = 0
    sink = 9
    intermediate = list(range(1, 9))  # nodes 1..8

    # Build outgoing and incoming arc sets per node
    out_arcs = {n: [] for n in range(10)}
    in_arcs = {n: [] for n in range(10)}
    for i, (u, v) in enumerate(arcs):
        out_arcs[u].append(i)
        in_arcs[v].append(i)

    # --- Phase 1: maximize flow ---
    model = gp.Model("phase1_maxflow")
    model.setParam("OutputFlag", 0)

    flow = model.addVars(num_arcs, lb=0.0, name="flow")

    # Capacity constraints
    for i in range(num_arcs):
        model.addConstr(flow[i] <= capacities[i], name=f"cap_{i}")

    # Flow conservation at intermediate nodes
    for node in intermediate:
        model.addConstr(
            gp.quicksum(flow[i] for i in in_arcs[node]) ==
            gp.quicksum(flow[i] for i in out_arcs[node]),
            name=f"conserve_{node}"
        )

    # Total flow leaving source
    total_flow = gp.quicksum(flow[i] for i in out_arcs[source])
    model.setObjective(total_flow, GRB.MAXIMIZE)

    model.optimize()

    if model.Status not in (GRB.OPTIMAL, GRB.SUBOPTIMAL):
        return {"objective": None, "status": "infeasible_phase1"}

    max_flow_val = model.ObjVal

    # --- Phase 2: minimize cost subject to achieving max flow ---
    model2 = gp.Model("phase2_mincost")
    model2.setParam("OutputFlag", 0)

    flow2 = model2.addVars(num_arcs, lb=0.0, name="flow")

    # Capacity constraints
    for i in range(num_arcs):
        model2.addConstr(flow2[i] <= capacities[i], name=f"cap_{i}")

    # Flow conservation at intermediate nodes
    for node in intermediate:
        model2.addConstr(
            gp.quicksum(flow2[i] for i in in_arcs[node]) ==
            gp.quicksum(flow2[i] for i in out_arcs[node]),
            name=f"conserve_{node}"
        )

    # Fix total flow to the maximum found in phase 1
    total_flow2 = gp.quicksum(flow2[i] for i in out_arcs[source])
    model2.addConstr(total_flow2 == max_flow_val, name="fix_flow")

    # Minimize total cost
    total_cost = gp.quicksum(unit_costs[i] * flow2[i] for i in range(num_arcs))
    model2.setObjective(total_cost, GRB.MINIMIZE)

    model2.optimize()

    if model2.Status not in (GRB.OPTIMAL, GRB.SUBOPTIMAL):
        return {"objective": None, "status": "infeasible_phase2"}

    return {"objective": float(model2.ObjVal), "status": "optimal"}