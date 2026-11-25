import gurobipy as gp
from gurobipy import GRB

def solve(params):
    edges = [
        (0, 1), (0, 3), (0, 5), (0, 6), (0, 7),
        (1, 2), (1, 4), (1, 5), (1, 6),
        (2, 4), (2, 7),
        (3, 4),
        (4, 5), (4, 6), (4, 7),
        (5, 7),
        (6, 7)
    ]
    nodes = list(range(8))

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(len(edges), vtype=GRB.BINARY, name="x")

    model.setObjective(gp.quicksum(x[i] for i in range(len(edges))), GRB.MAXIMIZE)

    for node in nodes:
        incident = [i for i, (u, v) in enumerate(edges) if u == node or v == node]
        if incident:
            model.addConstr(gp.quicksum(x[i] for i in incident) <= 1, name=f"node_{node}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}