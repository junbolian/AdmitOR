import gurobipy as gp
from gurobipy import GRB

def solve(params):
    supply_node0 = params["supply_node0"]
    demand_node5 = params["demand_node5"]

    # All directed edges (i, j) where i != j, for 6 nodes
    edges = [(i, j) for i in range(6) for j in range(6) if i != j]

    # Build cost dict from params
    cost = {}
    for (i, j) in edges:
        key = f"cost_{i}_{j}"
        cost[(i, j)] = params[key]

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary flow variables
    x = model.addVars(edges, vtype=GRB.BINARY, name="x")

    # Objective: minimize total cost
    model.setObjective(gp.quicksum(cost[(i, j)] * x[(i, j)] for (i, j) in edges), GRB.MINIMIZE)

    # Flow balance constraints
    # Node 0: outflow - inflow = supply_node0
    model.addConstr(
        gp.quicksum(x[(0, j)] for j in range(6) if j != 0) -
        gp.quicksum(x[(i, 0)] for i in range(6) if i != 0) == supply_node0,
        name="balance_0"
    )

    # Nodes 1-4: inflow = outflow (transshipment)
    for node in range(1, 5):
        model.addConstr(
            gp.quicksum(x[(i, node)] for i in range(6) if i != node) -
            gp.quicksum(x[(node, j)] for j in range(6) if j != node) == 0,
            name=f"balance_{node}"
        )

    # Node 5: inflow - outflow = demand_node5
    model.addConstr(
        gp.quicksum(x[(i, 5)] for i in range(6) if i != 5) -
        gp.quicksum(x[(5, j)] for j in range(6) if j != 5) == demand_node5,
        name="balance_5"
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}