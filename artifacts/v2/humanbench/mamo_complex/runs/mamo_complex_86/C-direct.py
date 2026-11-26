import gurobipy as gp
from gurobipy import GRB

def solve(params):
    capacity_1_2 = params["capacity_1_2"]
    capacity_1_3 = params["capacity_1_3"]
    capacity_2_3 = params["capacity_2_3"]
    capacity_2_4 = params["capacity_2_4"]
    capacity_3_4 = params["capacity_3_4"]

    # Edges: (from, to) -> capacity
    edges = {
        (1, 2): capacity_1_2,
        (1, 3): capacity_1_3,
        (2, 3): capacity_2_3,
        (2, 4): capacity_2_4,
        (3, 4): capacity_3_4,
    }

    nodes = [1, 2, 3, 4]
    source = 1
    sink = 4

    model = gp.Model("max_flow")
    model.setParam("OutputFlag", 0)

    # Flow variables for each edge
    flow = {}
    for (i, j), cap in edges.items():
        flow[(i, j)] = model.addVar(lb=0.0, ub=cap, name=f"flow_{i}_{j}")

    # Auxiliary variable for total flow out of source
    total_flow = model.addVar(lb=0.0, name="total_flow")

    model.setObjective(total_flow, GRB.MAXIMIZE)

    # Flow conservation constraints for intermediate nodes (not source/sink)
    for node in nodes:
        if node == source or node == sink:
            continue
        inflow = gp.quicksum(flow[(i, j)] for (i, j) in edges if j == node)
        outflow = gp.quicksum(flow[(i, j)] for (i, j) in edges if i == node)
        model.addConstr(inflow == outflow, name=f"conservation_{node}")

    # Source: outflow - inflow = total_flow
    source_outflow = gp.quicksum(flow[(i, j)] for (i, j) in edges if i == source)
    source_inflow = gp.quicksum(flow[(i, j)] for (i, j) in edges if j == source)
    model.addConstr(source_outflow - source_inflow == total_flow, name="source_flow")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": round(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}