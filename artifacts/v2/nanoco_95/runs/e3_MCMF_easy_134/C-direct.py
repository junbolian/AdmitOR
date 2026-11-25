import gurobipy as gp
from gurobipy import GRB

def solve(params):
    arcs = [
        (0, 1), (1, 2), (1, 4), (1, 5), (1, 7),
        (2, 3), (3, 4), (4, 5), (4, 8), (4, 9),
        (5, 6), (5, 7), (6, 7), (7, 8), (8, 9)
    ]

    capacity = {
        (0, 1): params["capacity_0_1"],
        (1, 2): params["capacity_1_2"],
        (1, 4): params["capacity_1_4"],
        (1, 5): params["capacity_1_5"],
        (1, 7): params["capacity_1_7"],
        (2, 3): params["capacity_2_3"],
        (3, 4): params["capacity_3_4"],
        (4, 5): params["capacity_4_5"],
        (4, 8): params["capacity_4_8"],
        (4, 9): params["capacity_4_9"],
        (5, 6): params["capacity_5_6"],
        (5, 7): params["capacity_5_7"],
        (6, 7): params["capacity_6_7"],
        (7, 8): params["capacity_7_8"],
        (8, 9): params["capacity_8_9"],
    }

    cost = {
        (0, 1): params["cost_0_1"],
        (1, 2): params["cost_1_2"],
        (1, 4): params["cost_1_4"],
        (1, 5): params["cost_1_5"],
        (1, 7): params["cost_1_7"],
        (2, 3): params["cost_2_3"],
        (3, 4): params["cost_3_4"],
        (4, 5): params["cost_4_5"],
        (4, 8): params["cost_4_8"],
        (4, 9): params["cost_4_9"],
        (5, 6): params["cost_5_6"],
        (5, 7): params["cost_5_7"],
        (6, 7): params["cost_6_7"],
        (7, 8): params["cost_7_8"],
        (8, 9): params["cost_8_9"],
    }

    source = 0
    sink = 9
    nodes = list(range(10))

    # Phase 1: maximize flow
    model = gp.Model()
    model.setParam("OutputFlag", 0)

    flow = model.addVars(arcs, lb=0.0, name="flow")

    # Capacity constraints
    for arc in arcs:
        model.addConstr(flow[arc] <= capacity[arc], name=f"cap_{arc[0]}_{arc[1]}")

    # Flow conservation for intermediate nodes
    for node in nodes:
        if node == source or node == sink:
            continue
        in_flow = gp.quicksum(flow[arc] for arc in arcs if arc[1] == node)
        out_flow = gp.quicksum(flow[arc] for arc in arcs if arc[0] == node)
        model.addConstr(in_flow == out_flow, name=f"conserve_{node}")

    # Total flow out of source
    total_flow = gp.quicksum(flow[arc] for arc in arcs if arc[0] == source)

    model.setObjective(total_flow, GRB.MAXIMIZE)
    model.optimize()

    if model.Status not in (GRB.OPTIMAL, GRB.SUBOPTIMAL):
        return {"objective": None, "status": "infeasible_phase1"}

    max_flow_value = model.ObjVal

    # Phase 2: minimize cost subject to achieving max flow
    model = gp.Model()
    model.setParam("OutputFlag", 0)

    flow = model.addVars(arcs, lb=0.0, name="flow")

    for arc in arcs:
        model.addConstr(flow[arc] <= capacity[arc], name=f"cap_{arc[0]}_{arc[1]}")

    for node in nodes:
        if node == source or node == sink:
            continue
        in_flow = gp.quicksum(flow[arc] for arc in arcs if arc[1] == node)
        out_flow = gp.quicksum(flow[arc] for arc in arcs if arc[0] == node)
        model.addConstr(in_flow == out_flow, name=f"conserve_{node}")

    total_flow2 = gp.quicksum(flow[arc] for arc in arcs if arc[0] == source)
    model.addConstr(total_flow2 == max_flow_value, name="fix_max_flow")

    total_cost = gp.quicksum(cost[arc] * flow[arc] for arc in arcs)
    model.setObjective(total_cost, GRB.MINIMIZE)
    model.optimize()

    if model.Status not in (GRB.OPTIMAL, GRB.SUBOPTIMAL):
        return {"objective": None, "status": "infeasible_phase2"}

    return {"objective": model.ObjVal, "status": "optimal"}