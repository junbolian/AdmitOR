import gurobipy as gp
from gurobipy import GRB

def solve(params):
    edge_capacities = params["edge_capacities"]
    source = params["source_node"]
    sink = params["sink_node"]
    n = params["num_cities"]

    # Build edge list from the description:
    # 0->1,0->2,...,0->8 (8 edges)
    # 1->0,1->2,1->4,1->5,1->6,1->7,1->8 (7 edges, skipping 1->3)
    # 2->0,2->1,2->4,2->5,2->6,2->7,2->8 (7 edges, skipping 2->3)
    # 3->0,3->1,3->2,3->4,3->5,3->6,3->7,3->8 (8 edges)
    # 4->0,4->1,4->2,4->3,4->5,4->6,4->7,4->8 (8 edges, skipping 4->4... wait no)
    # Actually per the params description, let's parse the order exactly.

    edge_list = []
    # 0->1,0->2,0->3,0->4,0->5,0->6,0->7,0->8
    for j in [1,2,3,4,5,6,7,8]:
        edge_list.append((0, j))
    # 1->0,1->2,1->4,1->5,1->6,1->7,1->8
    for j in [0,2,4,5,6,7,8]:
        edge_list.append((1, j))
    # 2->0,2->1,2->4,2->5,2->6,2->7,2->8
    for j in [0,1,4,5,6,7,8]:
        edge_list.append((2, j))
    # 3->0,3->1,3->2,3->4,3->5,3->6,3->7,3->8
    for j in [0,1,2,4,5,6,7,8]:
        edge_list.append((3, j))
    # 4->0,4->1,4->2,4->3,4->5,4->6,4->7,4->8
    for j in [0,1,2,3,5,6,7,8]:
        edge_list.append((4, j))
    # 5->0,5->1,5->2,5->3,5->4,5->6,5->7,5->8
    for j in [0,1,2,3,4,6,7,8]:
        edge_list.append((5, j))
    # 6->0,6->1,6->2,6->3,6->4,6->5,6->7,6->8
    for j in [0,1,2,3,4,5,7,8]:
        edge_list.append((6, j))
    # 7->0,7->1,7->2,7->3,7->4,7->5,7->6,7->8
    for j in [0,1,2,3,4,5,6,8]:
        edge_list.append((7, j))
    # 8->0,8->1,8->2,8->3,8->4,8->5,8->6,8->7
    for j in [0,1,2,3,4,5,6,7]:
        edge_list.append((8, j))

    capacity = {}
    for idx, (i, j) in enumerate(edge_list):
        capacity[(i, j)] = edge_capacities[idx]

    model = gp.Model("max_flow")
    model.setParam("OutputFlag", 0)

    # Flow variables
    flow = {}
    for (i, j) in edge_list:
        flow[(i, j)] = model.addVar(lb=0.0, ub=capacity[(i, j)], name=f"f_{i}_{j}")

    # Objective: maximize flow out of source
    model.setObjective(
        gp.quicksum(flow[(source, j)] for (i, j) in edge_list if i == source),
        GRB.MAXIMIZE
    )

    # Flow conservation for all nodes except source and sink
    for node in range(n):
        if node == source or node == sink:
            continue
        inflow = gp.quicksum(flow[(i, j)] for (i, j) in edge_list if j == node)
        outflow = gp.quicksum(flow[(i, j)] for (i, j) in edge_list if i == node)
        model.addConstr(inflow == outflow, name=f"conservation_{node}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}