import gurobipy as gp
from gurobipy import GRB

def solve(params):
    capacity = {
        (0, 1): params["capacity_0_1"],
        (0, 2): params["capacity_0_2"],
        (0, 3): params["capacity_0_3"],
        (0, 4): params["capacity_0_4"],
        (0, 5): params["capacity_0_5"],
        (1, 0): params["capacity_1_0"],
        (1, 2): params["capacity_1_2"],
        (1, 3): params["capacity_1_3"],
        (1, 5): params["capacity_1_5"],
        (2, 0): params["capacity_2_0"],
        (2, 1): params["capacity_2_1"],
        (2, 3): params["capacity_2_3"],
        (2, 4): params["capacity_2_4"],
        (3, 0): params["capacity_3_0"],
        (3, 1): params["capacity_3_1"],
        (3, 2): params["capacity_3_2"],
        (3, 4): params["capacity_3_4"],
        (4, 0): params["capacity_4_0"],
        (4, 2): params["capacity_4_2"],
        (4, 3): params["capacity_4_3"],
        (4, 5): params["capacity_4_5"],
        (5, 0): params["capacity_5_0"],
        (5, 1): params["capacity_5_1"],
        (5, 2): params["capacity_5_2"],
        (5, 3): params["capacity_5_3"],
        (5, 4): params["capacity_5_4"],
    }

    num_nodes = int(params["num_nodes"])
    source = int(params["source_node"])
    sink = int(params["sink_node"])

    nodes = list(range(num_nodes))
    edges = list(capacity.keys())

    model = gp.Model("max_flow")
    model.setParam("OutputFlag", 0)

    flow = model.addVars(edges, lb=0.0, name="flow")

    # Capacity constraints
    for (i, j) in edges:
        model.addConstr(flow[i, j] <= capacity[i, j], name=f"cap_{i}_{j}")

    # Flow conservation for intermediate nodes
    for node in nodes:
        if node == source or node == sink:
            continue
        inflow = gp.quicksum(flow[i, j] for (i, j) in edges if j == node)
        outflow = gp.quicksum(flow[i, j] for (i, j) in edges if i == node)
        model.addConstr(inflow == outflow, name=f"conservation_{node}")

    # Objective: maximize flow out of source
    total_flow = gp.quicksum(flow[i, j] for (i, j) in edges if i == source) \
               - gp.quicksum(flow[i, j] for (i, j) in edges if j == source)
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