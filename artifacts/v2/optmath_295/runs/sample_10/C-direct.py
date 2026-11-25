import gurobipy as gp
from gurobipy import GRB

def solve(params):
    nodes = list(range(7))
    # All directed edges (i, j) where i != j
    edges = [(i, j) for i in nodes for j in nodes if i != j]

    # Build cost dict from params
    cost = {}
    for (i, j) in edges:
        key = f"cost_{i}_{j}"
        cost[(i, j)] = params[key]

    supply_0 = params["supply_node_0"]
    demand_6 = params["demand_node_6"]

    model = gp.Model("shortest_path")
    model.setParam("OutputFlag", 0)

    # Binary flow variables
    x = model.addVars(edges, vtype=GRB.BINARY, name="x")

    # Objective: minimize total cost
    model.setObjective(gp.quicksum(cost[(i, j)] * x[(i, j)] for (i, j) in edges), GRB.MINIMIZE)

    # Flow balance constraints
    for node in nodes:
        outflow = gp.quicksum(x[(node, j)] for j in nodes if (node, j) in edges)
        inflow  = gp.quicksum(x[(i, node)] for i in nodes if (i, node) in edges)

        if node == 0:
            # Source: net outflow = supply_0
            model.addConstr(outflow - inflow == supply_0, name=f"balance_{node}")
        elif node == 6:
            # Sink: net inflow = demand_6
            model.addConstr(inflow - outflow == demand_6, name=f"balance_{node}")
        else:
            # Intermediate: flow conservation
            model.addConstr(inflow - outflow == 0, name=f"balance_{node}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}