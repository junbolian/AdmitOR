import gurobipy as gp
from gurobipy import GRB

def solve(params):
    # Feasible (task, server) pairs
    compatible = [
        (0, 3), (0, 4),
        (1, 0), (1, 3), (1, 4),
        (2, 0), (2, 3),
        (3, 1), (3, 2),
        (4, 0), (4, 1),
        (5, 2),
        (6, 0), (6, 3), (6, 4),
    ]

    tasks = range(7)
    servers = range(5)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    # Binary assignment variables only on compatible pairs
    x = model.addVars(compatible, vtype=GRB.BINARY, name="x")

    # Maximize total assignments
    model.setObjective(gp.quicksum(x[i, j] for (i, j) in compatible), GRB.MAXIMIZE)

    # Each task assigned to at most one server
    for i in tasks:
        pairs = [(i2, j) for (i2, j) in compatible if i2 == i]
        if pairs:
            model.addConstr(gp.quicksum(x[i2, j] for (i2, j) in pairs) <= 1, name=f"task_{i}")

    # Each server receives at most one task
    for j in servers:
        pairs = [(i, j2) for (i, j2) in compatible if j2 == j]
        if pairs:
            model.addConstr(gp.quicksum(x[i, j2] for (i, j2) in pairs) <= 1, name=f"server_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}