import gurobipy as gp
from gurobipy import GRB

def solve(params):
    edge_cost = params["edge_cost"]
    supply_node_0 = params["supply_node_0"]
    demand_node_7 = params["demand_node_7"]

    n = 8
    nodes = list(range(n))

    # Build list of directed edges (excluding self-loops) in row-major order
    edges = [(i, j) for i in nodes for j in nodes if i != j]
    # edge_cost is indexed accordingly
    cost = {edges[k]: edge_cost[k] for k in range(len(edges))}

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary flow variables for each directed edge
    x = model.addVars(edges, vtype=GRB.BINARY, name="x")

    # Objective: minimize total cost
    model.setObjective(gp.quicksum(cost[e] * x[e] for e in edges), GRB.MINIMIZE)

    # Flow balance constraints
    for i in nodes:
        outflow = gp.quicksum(x[i, j] for j in nodes if (i, j) in cost)
        inflow = gp.quicksum(x[j, i] for j in nodes if (j, i) in cost)
        if i == 0:
            model.addConstr(outflow - inflow == supply_node_0, name=f"balance_{i}")
        elif i == 7:
            model.addConstr(inflow - outflow == demand_node_7, name=f"balance_{i}")
        else:
            model.addConstr(outflow - inflow == 0, name=f"balance_{i}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}