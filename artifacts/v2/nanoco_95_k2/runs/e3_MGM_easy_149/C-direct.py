import gurobipy as gp
from gurobipy import GRB

def solve(params):
    edges = [
        (0, 1), (0, 4), (0, 5),
        (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7),
        (2, 5),
        (3, 4), (3, 7),
        (4, 6), (4, 7),
        (5, 6), (5, 7),
        (6, 7),
    ]

    nodes = list(range(8))

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(edges, vtype=GRB.BINARY, name="x")

    model.setObjective(gp.quicksum(x[e] for e in edges), GRB.MAXIMIZE)

    for node in nodes:
        incident = [e for e in edges if e[0] == node or e[1] == node]
        if incident:
            model.addConstr(gp.quicksum(x[e] for e in incident) <= 1, name=f"node_{node}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}