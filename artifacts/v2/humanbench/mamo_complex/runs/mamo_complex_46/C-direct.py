import gurobipy as gp
from gurobipy import GRB

def solve(params):
    # Build capacity matrix from params
    # Nodes 0..7, source=0, sink=7
    n = 8
    
    # Initialize capacity dict
    cap = {}
    
    # From node 0
    cap[(0,1)] = params["capacity_0_1"]
    cap[(0,2)] = params["capacity_0_2"]
    cap[(0,3)] = params["capacity_0_3"]
    cap[(0,4)] = params["capacity_0_4"]
    cap[(0,5)] = params["capacity_0_5"]
    cap[(0,6)] = params["capacity_0_6"]
    cap[(0,7)] = params["capacity_0_7"]
    
    # From node 1 to [0,2,3,4,5,6,7]
    caps_1 = params["capacities_from_1"]
    targets_1 = [0,2,3,4,5,6,7]
    for idx, j in enumerate(targets_1):
        cap[(1,j)] = caps_1[idx]
    
    # From node 2 to [0,1,3,4,5,6,7]
    caps_2 = params["capacities_from_2"]
    targets_2 = [0,1,3,4,5,6,7]
    for idx, j in enumerate(targets_2):
        cap[(2,j)] = caps_2[idx]
    
    # From node 3 to [0,1,2,4,5,6,7]
    caps_3 = params["capacities_from_3"]
    targets_3 = [0,1,2,4,5,6,7]
    for idx, j in enumerate(targets_3):
        cap[(3,j)] = caps_3[idx]
    
    # From node 4 to [0,1,2,3,5,6,7]
    caps_4 = params["capacities_from_4"]
    targets_4 = [0,1,2,3,5,6,7]
    for idx, j in enumerate(targets_4):
        cap[(4,j)] = caps_4[idx]
    
    # From node 5 to [0,1,2,3,4,6,7]
    caps_5 = params["capacities_from_5"]
    targets_5 = [0,1,2,3,4,6,7]
    for idx, j in enumerate(targets_5):
        cap[(5,j)] = caps_5[idx]
    
    # From node 6 to [0,1,2,3,4,5,7]
    caps_6 = params["capacities_from_6"]
    targets_6 = [0,1,2,3,4,5,7]
    for idx, j in enumerate(targets_6):
        cap[(6,j)] = caps_6[idx]
    
    # From node 7 to [0,1,2,3,4,5,6]
    caps_7 = params["capacities_from_7"]
    targets_7 = [0,1,2,3,4,5,6]
    for idx, j in enumerate(targets_7):
        cap[(7,j)] = caps_7[idx]
    
    # Build list of valid arcs (capacity > 0)
    arcs = [(i, j) for (i, j), c in cap.items() if c > 0]
    
    source = 0
    sink = 7
    
    model = gp.Model("max_flow")
    model.setParam("OutputFlag", 0)
    
    # Flow variables
    flow = model.addVars(arcs, lb=0.0, name="flow")
    
    # Capacity constraints
    for (i, j) in arcs:
        model.addConstr(flow[i, j] <= cap[(i, j)], name=f"cap_{i}_{j}")
    
    # Flow conservation for intermediate nodes
    nodes = list(range(n))
    for node in nodes:
        if node == source or node == sink:
            continue
        in_flow = gp.quicksum(flow[i, node] for (i, j) in arcs if j == node)
        out_flow = gp.quicksum(flow[node, j] for (i, j) in arcs if i == node)
        model.addConstr(in_flow == out_flow, name=f"conservation_{node}")
    
    # Objective: maximize flow into sink
    obj = gp.quicksum(flow[i, sink] for (i, j) in arcs if j == sink)
    model.setObjective(obj, GRB.MAXIMIZE)
    
    model.optimize()
    
    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}