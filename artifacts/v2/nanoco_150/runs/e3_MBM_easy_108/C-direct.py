import gurobipy as gp
from gurobipy import GRB

def solve(params):
    # Feasible (patient, room) pairs
    compatible = [
        (0, 0), (0, 2), (0, 4), (0, 5),
        (1, 2), (1, 6),
        (2, 0), (2, 2), (2, 3),
        (3, 0), (3, 4),
        (4, 1), (4, 2), (4, 3), (4, 4),
    ]

    patients = range(5)
    rooms = range(7)

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(compatible, vtype=GRB.BINARY, name="x")

    # Maximize total assignments
    model.setObjective(gp.quicksum(x[p, r] for p, r in compatible), GRB.MAXIMIZE)

    # Each patient assigned to at most one room
    for p in patients:
        pairs = [(p2, r) for p2, r in compatible if p2 == p]
        if pairs:
            model.addConstr(gp.quicksum(x[p2, r] for p2, r in pairs) <= 1, name=f"patient_{p}")

    # Each room receives at most one patient
    for r in rooms:
        pairs = [(p, r2) for p, r2 in compatible if r2 == r]
        if pairs:
            model.addConstr(gp.quicksum(x[p, r2] for p, r2 in pairs) <= 1, name=f"room_{r}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}