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

    # Capacity constraints
    for edge in edges:
        model.addConstr(flow[edge] <= capacity[edge], name=f"cap_{edge[0]}_{edge[1]}")

    # Flow conservation for intermediate nodes
    for node in intermediate_nodes:
        inflow = gp.quicksum(flow[e] for e in edges if e[1] == node)
        outflow = gp.quicksum(flow[e] for e in edges if e[0] == node)
        model.addConstr(inflow == outflow, name=f"conserve_{node}")

    # Total flow into sink
    total_flow = gp.quicksum(flow[e] for e in edges if e[1] == sink)

    # Maximize total flow into sink
    model.setObjective(total_flow, GRB.MAXIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}