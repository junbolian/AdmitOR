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

    # Phase 1: maximize flow
    model = gp.Model()
    model.setParam("OutputFlag", 0)

    flow = model.addVars(arcs, lb=0.0, name="flow")

    # Capacity constraints
    for arc in arcs:
        model.addConstr(flow[arc] <= cap[arc], name=f"cap_{arc[0]}_{arc[1]}")

    # Flow conservation for intermediate nodes
    for nd in nodes:
        if nd == source or nd == sink:
            continue
        in_flow = gp.quicksum(flow[(i, j)] for (i, j) in arcs if j == nd)
        out_flow = gp.quicksum(flow[(i, j)] for (i, j) in arcs if i == nd)
        model.addConstr(in_flow == out_flow, name=f"conservation_{nd}")

    # Total flow leaving source
    total_flow = gp.quicksum(flow[(i, j)] for (i, j) in arcs if i == source)

    model.setObjective(total_flow, GRB.MAXIMIZE)
    model.optimize()

    if model.Status not in (GRB.OPTIMAL, GRB.SUBOPTIMAL):
        return {"objective": None, "status": "infeasible_phase1"}

    max_throughput = model.ObjVal

    # Phase 2: minimize cost subject to achieving max_throughput
    model2 = gp.Model()
    model2.setParam("OutputFlag", 0)

    flow2 = model2.addVars(arcs, lb=0.0, name="flow2")

    for arc in arcs:
        model2.addConstr(flow2[arc] <= cap[arc], name=f"cap_{arc[0]}_{arc[1]}")

    for nd in nodes:
        if nd == source or nd == sink:
            continue
        in_flow2 = gp.quicksum(flow2[(i, j)] for (i, j) in arcs if j == nd)
        out_flow2 = gp.quicksum(flow2[(i, j)] for (i, j) in arcs if i == nd)
        model2.addConstr(in_flow2 == out_flow2, name=f"conservation_{nd}")

    total_flow2 = gp.quicksum(flow2[(i, j)] for (i, j) in arcs if i == source)
    model2.addConstr(total_flow2 >= max_throughput - 1e-6, name="min_throughput")

    total_cost = gp.quicksum(cost[arc] * flow2[arc] for arc in arcs)
    model2.setObjective(total_cost, GRB.MINIMIZE)
    model2.optimize()

    if model2.Status not in (GRB.OPTIMAL, GRB.SUBOPTIMAL):
        return {"objective": None, "status": "infeasible_phase2"}

    return {"objective": model2.ObjVal, "status": "optimal"}