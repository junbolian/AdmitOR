import gurobipy as gp
from gurobipy import GRB

def solve(params):
    # Build capacity dict from params
    cap = {}
    cap[(0,1)] = params["cap_0_1"]
    cap[(0,2)] = params["cap_0_2"]
    cap[(0,3)] = params["cap_0_3"]
    cap[(0,4)] = params["cap_0_4"]
    cap[(0,5)] = params["cap_0_5"]
    cap[(0,6)] = params["cap_0_6"]
    cap[(1,0)] = params["cap_1_0"]
    cap[(1,2)] = params["cap_1_2"]
    cap[(1,3)] = params["cap_1_3"]
    cap[(1,4)] = params["cap_1_4"]
    cap[(1,5)] = params["cap_1_5"]
    cap[(2,0)] = params["cap_2_0"]
    cap[(2,1)] = params["cap_2_1"]
    cap[(2,3)] = params["cap_2_3"]
    cap[(2,5)] = params["cap_2_5"]
    cap[(2,6)] = params["cap_2_6"]
    cap[(3,0)] = params["cap_3_0"]
    cap[(3,1)] = params["cap_3_1"]
    cap[(3,2)] = params["cap_3_2"]
    cap[(3,4)] = params["cap_3_4"]
    cap[(3,5)] = params["cap_3_5"]
    cap[(3,6)] = params["cap_3_6"]
    cap[(4,0)] = params["cap_4_0"]
    cap[(4,1)] = params["cap_4_1"]
    cap[(4,2)] = params["cap_4_2"]
    cap[(4,3)] = params["cap_4_3"]
    cap[(4,5)] = params["cap_4_5"]
    cap[(4,6)] = params["cap_4_6"]
    cap[(5,0)] = params["cap_5_0"]
    cap[(5,1)] = params["cap_5_1"]
    cap[(5,2)] = params["cap_5_2"]
    cap[(5,3)] = params["cap_5_3"]
    cap[(5,4)] = params["cap_5_4"]
    cap[(5,6)] = params["cap_5_6"]
    cap[(6,0)] = params["cap_6_0"]
    cap[(6,1)] = params["cap_6_1"]
    cap[(6,2)] = params["cap_6_2"]
    cap[(6,3)] = params["cap_6_3"]
    cap[(6,4)] = params["cap_6_4"]
    cap[(6,5)] = params["cap_6_5"]

    source = 0
    sink = 6
    nodes = list(range(7))
    edges = list(cap.keys())

    model = gp.Model("max_flow")
    model.setParam("OutputFlag", 0)

    # Flow variables
    flow = model.addVars(edges, lb=0.0, name="flow")

    # Capacity constraints
    for (i, j) in edges:
        model.addConstr(flow[i, j] <= cap[(i, j)], name=f"cap_{i}_{j}")

    # Flow conservation for intermediate nodes
    for node in nodes:
        if node == source or node == sink:
            continue
        in_edges = [(i, j) for (i, j) in edges if j == node]
        out_edges = [(i, j) for (i, j) in edges if i == node]
        model.addConstr(
            gp.quicksum(flow[i, j] for (i, j) in in_edges) ==
            gp.quicksum(flow[i, j] for (i, j) in out_edges),
            name=f"conservation_{node}"
        )

    # Objective: maximize flow out of source
    out_source = [(i, j) for (i, j) in edges if i == source]
    in_source = [(i, j) for (i, j) in edges if j == source]
    total_flow = gp.quicksum(flow[i, j] for (i, j) in out_source) - \
                 gp.quicksum(flow[i, j] for (i, j) in in_source)

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