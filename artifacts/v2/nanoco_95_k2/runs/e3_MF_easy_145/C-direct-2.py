import gurobipy as gp
from gurobipy import GRB

def solve(params):
    edges = [
        (0, 1), (0, 2), (0, 6), (0, 8),
        (1, 2), (1, 5),
        (2, 3), (2, 6),
        (3, 4),
        (4, 5),
        (5, 6),
        (6, 7), (6, 8),
        (7, 8),
    ]

    capacity = {
        (0, 1): params["capacity_0_1"],
        (0, 2): params["capacity_0_2"],
        (0, 6): params["capacity_0_6"],
        (0, 8): params["capacity_0_8"],
        (1, 2): params["capacity_1_2"],
        (1, 5): params["capacity_1_5"],
        (2, 3): params["capacity_2_3"],
        (2, 6): params["capacity_2_6"],
        (3, 4): params["capacity_3_4"],
        (4, 5): params["capacity_4_5"],
        (5, 6): params["capacity_5_6"],
        (6, 7): params["capacity_6_7"],
        (6, 8): params["capacity_6_8"],
        (7, 8): params["capacity_7_8"],
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

    source = 0
    sink = 8
    intermediate_nodes = [1, 2, 3, 4, 5, 6, 7]

    model = gp.Model("max_flow")
    model.setParam("OutputFlag", 0)

    # Flow variables for each edge
    flow = model.addVars(edges, lb=0.0, name="flow")

    # Total flow variable (auxiliary, equal to outflow from source)
    total_flow = model.addVar(lb=0.0, name="total_flow")

    # Maximize total flow from source to sink
    model.setObjective(total_flow, GRB.MAXIMIZE)

    # Capacity constraints
    for (i, j) in edges:
        model.addConstr(flow[i, j] <= capacity[i, j], name=f"cap_{i}_{j}")

    # Source node: outflow - inflow = total_flow
    out_source = gp.quicksum(flow[i, j] for (i, j) in edges if i == source)
    in_source  = gp.quicksum(flow[i, j] for (i, j) in edges if j == source)
    model.addConstr(out_source - in_source == total_flow, name="source_balance")

    # Sink node: inflow - outflow = total_flow
    in_sink  = gp.quicksum(flow[i, j] for (i, j) in edges if j == sink)
    out_sink = gp.quicksum(flow[i, j] for (i, j) in edges if i == sink)
    model.addConstr(in_sink - out_sink == total_flow, name="sink_balance")

    # Flow conservation for intermediate nodes
    for node in intermediate_nodes:
        in_flow  = gp.quicksum(flow[i, j] for (i, j) in edges if j == node)
        out_flow = gp.quicksum(flow[i, j] for (i, j) in edges if i == node)
        model.addConstr(in_flow == out_flow, name=f"conservation_{node}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}