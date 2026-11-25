import gurobipy as gp
from gurobipy import GRB

def solve(params):
    capacities = params["capacities"]
    costs = params["costs"]
    source_node = params["source_node"]
    sink_node = params["sink_node"]
    num_nodes = params["num_nodes"]
    num_arcs = params["num_arcs"]

    arcs = [
        (0, 1), (1, 2), (1, 7), (2, 3), (2, 6),
        (3, 4), (3, 8), (3, 9), (4, 5), (4, 8),
        (5, 6), (6, 7), (7, 8), (7, 9), (8, 9)
    ]

    assert len(arcs) == num_arcs, "Arc count mismatch"

    # Phase 1: maximize flow
    model = gp.Model("max_flow")
    model.setParam("OutputFlag", 0)

    flow = model.addVars(num_arcs, lb=0.0, name="flow")

    # Capacity constraints
    for i in range(num_arcs):
        model.addConstr(flow[i] <= capacities[i], name=f"cap_{i}")

    # Flow conservation for intermediate nodes
    for node in range(num_nodes):
        if node == source_node or node == sink_node:
            continue
        in_arcs = [i for i, (u, v) in enumerate(arcs) if v == node]
        out_arcs = [i for i, (u, v) in enumerate(arcs) if u == node]
        model.addConstr(
            gp.quicksum(flow[i] for i in in_arcs) ==
            gp.quicksum(flow[i] for i in out_arcs),
            name=f"conservation_{node}"
        )

    # Objective: maximize total flow out of source
    source_out = [i for i, (u, v) in enumerate(arcs) if u == source_node]
    source_in  = [i for i, (u, v) in enumerate(arcs) if v == source_node]
    total_flow = gp.quicksum(flow[i] for i in source_out) - gp.quicksum(flow[i] for i in source_in)
    model.setObjective(total_flow, GRB.MAXIMIZE)

    model.optimize()

    if model.Status not in (GRB.OPTIMAL, GRB.SUBOPTIMAL):
        return {"objective": None, "status": "infeasible_or_unbounded"}

    max_flow_value = model.ObjVal

    # Phase 2: minimize cost subject to achieving max flow
    model2 = gp.Model("min_cost_max_flow")
    model2.setParam("OutputFlag", 0)

    flow2 = model2.addVars(num_arcs, lb=0.0, name="flow2")

    # Capacity constraints
    for i in range(num_arcs):
        model2.addConstr(flow2[i] <= capacities[i], name=f"cap_{i}")

    # Flow conservation for intermediate nodes
    for node in range(num_nodes):
        if node == source_node or node == sink_node:
            continue
        in_arcs = [i for i, (u, v) in enumerate(arcs) if v == node]
        out_arcs = [i for i, (u, v) in enumerate(arcs) if u == node]
        model2.addConstr(
            gp.quicksum(flow2[i] for i in in_arcs) ==
            gp.quicksum(flow2[i] for i in out_arcs),
            name=f"conservation_{node}"
        )

    # Fix total flow to max
    source_out2 = [i for i, (u, v) in enumerate(arcs) if u == source_node]
    source_in2  = [i for i, (u, v) in enumerate(arcs) if v == source_node]
    total_flow2 = (
        gp.quicksum(flow2[i] for i in source_out2) -
        gp.quicksum(flow2[i] for i in source_in2)
    )
    model2.addConstr(total_flow2 == max_flow_value, name="fix_max_flow")

    # Minimize cost
    model2.setObjective(
        gp.quicksum(costs[i] * flow2[i] for i in range(num_arcs)),
        GRB.MINIMIZE
    )

    model2.optimize()

    if model2.Status not in (GRB.OPTIMAL, GRB.SUBOPTIMAL):
        return {"objective": None, "status": "phase2_infeasible"}

    return {
        "objective": model2.ObjVal,
        "status": "optimal"
    }