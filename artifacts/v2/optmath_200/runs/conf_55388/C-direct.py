import gurobipy as gp
from gurobipy import GRB

def solve(params):
    # Extract parameters
    supply_node_0 = params["supply_node_0"]
    demand_node_6 = params["demand_node_6"]

    # All directed edges (i, j) where i != j, nodes 0-6
    edges = [
        (0,1),(0,2),(0,3),(0,4),(0,5),(0,6),
        (1,0),(1,2),(1,3),(1,4),(1,5),(1,6),
        (2,0),(2,1),(2,3),(2,4),(2,5),(2,6),
        (3,0),(3,1),(3,2),(3,4),(3,5),(3,6),
        (4,0),(4,1),(4,2),(4,3),(4,5),(4,6),
        (5,0),(5,1),(5,2),(5,3),(5,4),(5,6),
        (6,0),(6,1),(6,2),(6,3),(6,4),(6,5),
    ]

    cost = {}
    for (i, j) in edges:
        key = f"cost_{i}_{j}"
        cost[(i, j)] = params[key]

    model = gp.Model("min_cost_flow_binary")
    model.setParam("OutputFlag", 0)

    # Binary flow variables
    x = model.addVars(edges, vtype=GRB.BINARY, name="x")

    # Objective: minimize total transportation cost
    model.setObjective(gp.quicksum(cost[(i, j)] * x[i, j] for (i, j) in edges), GRB.MINIMIZE)

    # Flow balance constraints
    nodes = range(7)
    for node in nodes:
        outflow = gp.quicksum(x[i, j] for (i, j) in edges if i == node)
        inflow = gp.quicksum(x[i, j] for (i, j) in edges if j == node)
        if node == 0:
            # net supply: outflow - inflow = supply_node_0
            model.addConstr(outflow - inflow == supply_node_0, name=f"balance_{node}")
        elif node == 6:
            # net demand: inflow - outflow = demand_node_6
            model.addConstr(inflow - outflow == demand_node_6, name=f"balance_{node}")
        else:
            # balanced nodes
            model.addConstr(outflow - inflow == 0, name=f"balance_{node}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}