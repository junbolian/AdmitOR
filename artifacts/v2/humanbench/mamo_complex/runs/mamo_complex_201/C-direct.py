import gurobipy as gp
from gurobipy import GRB

def solve(params):
    cap = {
        (1, 2): params["capacity_1_2"],
        (1, 3): params["capacity_1_3"],
        (2, 3): params["capacity_2_3"],
        (2, 4): params["capacity_2_4"],
        (3, 4): params["capacity_3_4"],
    }

    nodes = [1, 2, 3, 4]
    source = 1
    sink = 4

    model = gp.Model("max_flow")
    model.setParam("OutputFlag", 0)

    flow = model.addVars(cap.keys(), lb=0.0, name="flow")

    # Capacity constraints
    for edge, c in cap.items():
        model.addConstr(flow[edge] <= c, name=f"cap_{edge[0]}_{edge[1]}")

    # Flow conservation for intermediate nodes
    for node in nodes:
        if node == source or node == sink:
            continue
        in_flow = gp.quicksum(flow[e] for e in cap if e[1] == node)
        out_flow = gp.quicksum(flow[e] for e in cap if e[0] == node)
        model.addConstr(in_flow == out_flow, name=f"conservation_{node}")

    # Objective: maximize flow into sink
    total_flow = gp.quicksum(flow[e] for e in cap if e[1] == sink)
    model.setObjective(total_flow, GRB.MAXIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": round(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}