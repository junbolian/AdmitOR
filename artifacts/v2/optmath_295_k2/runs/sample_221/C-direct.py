import gurobipy as gp
from gurobipy import GRB

def solve(params):
    edge_costs = params["edge_costs"]
    source_excess = params["node0_outflow_inflow_excess"]
    sink_excess = params["node7_inflow_outflow_excess"]

    n = 8
    # Build edge list: all directed edges i->j for i != j, ordered as described
    edges = []
    for i in range(n):
        for j in range(n):
            if i != j:
                edges.append((i, j))
    # edges has 56 entries matching the ordering in edge_costs

    cost = {edges[k]: edge_costs[k] for k in range(len(edges))}

    model = gp.Model("shortest_path")
    model.setParam("OutputFlag", 0)

    # Binary flow variables
    x = model.addVars(edges, vtype=GRB.BINARY, name="x")

    # Objective: minimize total cost
    model.setObjective(gp.quicksum(cost[e] * x[e] for e in edges), GRB.MINIMIZE)

    # Flow balance constraints
    for node in range(n):
        outflow = gp.quicksum(x[(node, j)] for j in range(n) if j != node)
        inflow = gp.quicksum(x[(i, node)] for i in range(n) if i != node)
        if node == 0:
            # outflow - inflow = source_excess
            model.addConstr(outflow - inflow == source_excess, name=f"balance_{node}")
        elif node == 7:
            # inflow - outflow = sink_excess
            model.addConstr(inflow - outflow == sink_excess, name=f"balance_{node}")
        else:
            # inflow == outflow
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