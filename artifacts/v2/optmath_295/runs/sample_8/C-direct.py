import gurobipy as gp
from gurobipy import GRB

def solve(params):
    arc_cost = params["arc_cost"]
    net_outflow_node_0 = params["net_outflow_node_0"]
    net_inflow_node_7 = params["net_inflow_node_7"]

    num_nodes = 8
    nodes = list(range(num_nodes))

    # Build arc list (all directed pairs excluding self-loops)
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    # Map arc_cost (row-major, omitting self-loops) to (i, j) keys
    # arc_cost is a flat list of length 8*7 = 56
    cost = {}
    idx = 0
    for i in nodes:
        for j in nodes:
            if i != j:
                cost[(i, j)] = arc_cost[idx]
                idx += 1

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary flow variables
    x = model.addVars(arcs, vtype=GRB.BINARY, name="x")

    # Objective: minimize total cost
    model.setObjective(
        gp.quicksum(cost[(i, j)] * x[i, j] for (i, j) in arcs),
        GRB.MINIMIZE
    )

    # Flow balance constraints
    for node in nodes:
        outflow = gp.quicksum(x[node, j] for j in nodes if j != node)
        inflow  = gp.quicksum(x[i, node] for i in nodes if i != node)

        if node == 0:
            model.addConstr(outflow - inflow == net_outflow_node_0, name=f"balance_{node}")
        elif node == 7:
            model.addConstr(inflow - outflow == net_inflow_node_7, name=f"balance_{node}")
        else:
            model.addConstr(inflow - outflow == 0, name=f"balance_{node}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}