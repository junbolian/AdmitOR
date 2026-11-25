import gurobipy as gp
from gurobipy import GRB


def solve(params):
    capacity = params["capacity"]
    values = params["values"]
    weights = params["weights"]

    n = len(values)  # 25 crops

    model = gp.Model("crop_selection")
    model.Params.OutputFlag = 0

    x = model.addVars(n, vtype=GRB.BINARY, name="x")

    model.setObjective(
        gp.quicksum(values[i] * x[i] for i in range(n)),
        GRB.MAXIMIZE,
    )

    model.addConstr(
        gp.quicksum(weights[i] * x[i] for i in range(n)) <= capacity,
        name="capacity",
    )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    else:
        return {"objective": None, "status": "no_optimal"}