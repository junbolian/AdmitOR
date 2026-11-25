import gurobipy as gp
from gurobipy import GRB

def solve(params):
    arcs = [
        (0, 1), (0, 2), (0, 6), (0, 8),
        (1, 2), (1, 5),
        (2, 3), (2, 6),
        (3, 4),
        (4, 5),
        (5, 6),
        (6, 7), (6, 8),
        (7, 8),
    ]

    cap = {
        (0, 1): params["cap_0_1"],
        (0, 2): params["cap_0_2"],
        (0, 6): params["cap_0_6"],
        (0, 8): params["cap_0_8"],
        (1, 2): params["cap_1_2"],
        (1, 5): params["cap_1_5"],
        (2, 3): params["cap_2_3"],
        (2, 6): params["cap_2_6"],
        (3, 4): params["cap_3_4"],
        (4, 5): params["cap_4_5"],
        (5, 6): params["cap_5_6"],
        (6, 7): params["cap_6_7"],
        (6, 8): params["cap_6_8"],
        (7, 8): params["cap_7_8"],
    }

    cost = {
        (0, 1): params["cost_0_1"],
        (0, 2): params["cost_0_2"],
        (0, 6): params["cost_0_6"],
        (0, 8): params["cost_0_8"],
        (1, 2): params["cost_1_2"],
        (1, 5): params["cost_1_5"],
        (2, 3): params["cost_2_3"],
        (2, 6): params["cost_2_6"],
        (3, 4): params["cost_3_4"],
        (4, 5): params["cost_4_5"],
        (5, 6): params["cost_5_6"],
        (6, 7): params["cost_6_7"],
        (6, 8): params["cost_6_8"],
        (7, 8): params["cost_7_8"],
    }

    nodes = list(range(9))
    source = 0
    sink = 8

    # Build outgoing and incoming arc sets per node
    out_arcs = {n: [] for n in nodes}
    in_arcs  = {n: [] for n in nodes}
    for (i, j) in arcs:
        out_arcs[i].append((i, j))
        in_arcs[j].append((i, j))

    # --- Phase 1: maximize throughput ---
    model = gp.Model("max_flow_phase1")
    model.setParam("OutputFlag", 0)

    flow = model.addVars(arcs, lb=0.0, name="flow")

    # Capacity constraints
    for arc in arcs:
        model.addConstr(flow[arc] <= cap[arc], name=f"cap_{arc[0]}_{arc[1]}")

    # Flow conservation for intermediate nodes
    for n in nodes:
        if n == source or n == sink:
            continue
        model.addConstr(
            gp.quicksum(flow[a] for a in out_arcs[n]) ==
            gp.quicksum(flow[a] for a in in_arcs[n]),
            name=f"conserve_{n}"
        )

    # Throughput variable = net flow out of source
    throughput = model.addVar(lb=0.0, name="throughput")
    model.addConstr(
        throughput ==
        gp.quicksum(flow[a] for a in out_arcs[source]) -
        gp.quicksum(flow[a] for a in in_arcs[source]),
        name="throughput_def"
    )

    model.setObjective(throughput, GRB.MAXIMIZE)
    model.optimize()

    if model.Status not in (GRB.OPTIMAL, GRB.SUBOPTIMAL):
        return {"objective": None, "status": "infeasible_phase1"}

    max_throughput = model.ObjVal

    # --- Phase 2: minimize cost subject to throughput = max_throughput ---
    model2 = gp.Model("min_cost_phase2")
    model2.setParam("OutputFlag", 0)

    flow2 = model2.addVars(arcs, lb=0.0, name="flow")

    for arc in arcs:
        model2.addConstr(flow2[arc] <= cap[arc], name=f"cap_{arc[0]}_{arc[1]}")

    for n in nodes:
        if n == source or n == sink:
            continue
        model2.addConstr(
            gp.quicksum(flow2[a] for a in out_arcs[n]) ==
            gp.quicksum(flow2[a] for a in in_arcs[n]),
            name=f"conserve_{n}"
        )

    throughput2 = model2.addVar(lb=0.0, name="throughput")
    model2.addConstr(
        throughput2 ==
        gp.quicksum(flow2[a] for a in out_arcs[source]) -
        gp.quicksum(flow2[a] for a in in_arcs[source]),
        name="throughput_def"
    )

    # Fix throughput to the maximum found in phase 1
    model2.addConstr(throughput2 == max_throughput, name="fix_throughput")

    total_cost = gp.quicksum(cost[a] * flow2[a] for a in arcs)
    model2.setObjective(total_cost, GRB.MINIMIZE)
    model2.optimize()

    if model2.Status not in (GRB.OPTIMAL, GRB.SUBOPTIMAL):
        return {"objective": None, "status": "infeasible_phase2"}

    return {
        "objective": float(max_throughput),
        "status": "optimal",
    }