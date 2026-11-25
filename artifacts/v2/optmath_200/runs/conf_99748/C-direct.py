import gurobipy as gp
from gurobipy import GRB

def solve(params):
    nodes = [0, 1, 2, 3, 4]

    interaction = {}
    for i in nodes:
        for j in nodes:
            if i != j:
                interaction[(i, j)] = params[f"interaction_score_{i}_{j}"]

    model = gp.Model("facility_placement")
    model.Params.OutputFlag = 0
    model.Params.NonConvex = 2

    x = {}
    for i in nodes:
        x[i] = model.addVar(vtype=GRB.BINARY, name=f"x_{i}")

    model.addConstr(gp.quicksum(x[i] for i in nodes) == 2, name="select_two")

    obj = gp.QuadExpr()
    for i in nodes:
        for j in nodes:
            if i != j:
                obj += interaction[(i, j)] * x[i] * x[j]

    model.setObjective(obj, GRB.MAXIMIZE)
    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    else:
        return {"objective": None, "status": "failed"}