import gurobipy as gp
from gurobipy import GRB

def solve(params):
    edges = [
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

    capacity = {
        (0, 1): params["capacity_0_1"],
        (0, 6): params["capacity_0_6"],
        (0, 8): params["capacity_0_8"],
        (1, 2): params["capacity_1_2"],
        (2, 3): params["capacity_2_3"],
        (2, 7): params["capacity_2_7"],
        (3, 4): params["capacity_3_4"],
        (4, 5): params["capacity_4_5"],
        (4, 7): params["capacity_4_7"],
        (4, 8): params["capacity_4_8"],
        (5, 6): params["capacity_5_6"],
        (6, 7): params["capacity_6_7"],
        (6, 8): params["capacity_6_8"],
        (7, 8): params["capacity_7_8"],
        (8, 9): params["capacity_8_9"],
    }

    source = 0
    sink = 9
    intermediate_nodes = list(range(1, 9))

    model = gp.Model("max_flow")
    model.setParam("OutputFlag", 0)

    flow = model.addVars(edges, lb=0.0, name="flow")

    for (i, j) in edges:
        model.addConstr(flow[i, j] <= capacity[i, j], name=f"cap_{i}_{j}")

    for node in intermediate_nodes:
        inflow = gp.quicksum(flow[i, j] for (i, j) in edges if j == node)
        outflow = gp.quicksum(flow[i, j] for (i, j) in edges if i == node)
        model.addConstr(inflow == outflow, name=f"conserve_{node}")

    total_flow = gp.quicksum(flow[source, j] for (i, j) in edges if i == source)
    model.setObjective(total_flow, GRB.MAXIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}