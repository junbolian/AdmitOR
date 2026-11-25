import gurobipy as gp
from gurobipy import GRB


def solve(params):
    edges = [
        (0, 1), (0, 2), (0, 3), (0, 4), (0, 6), (0, 7),
        (1, 2), (1, 3), (1, 4), (1, 5),
        (2, 3),
        (3, 5), (3, 6), (3, 7),
        (4, 5),
        (5, 6),
        (6, 7),
    ]

    nodes = range(8)

    model = gp.Model("max_cardinality_matching")
    model.Params.OutputFlag = 0

    x = {}
    for i, j in edges:
        x[i, j] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}_{j}")

    model.update()

    for n in nodes:
        incident = [x[i, j] for (i, j) in edges if i == n or j == n]
        if incident:
            model.addConstr(gp.quicksum(incident) <= 1, name=f"node_{n}")

    model.setObjective(gp.quicksum(x.values()), GRB.MAXIMIZE)
    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}

    return {"objective": None, "status": f"status_{model.Status}"}