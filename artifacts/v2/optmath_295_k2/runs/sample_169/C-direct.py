import gurobipy as gp
from gurobipy import GRB


def solve(params):
    capacity = params["capacity"]
    values = params["values"]
    weights = params["weights"]

    items = range(len(values))

    model = gp.Model("crop_selection")
    model.Params.OutputFlag = 0

    x = model.addVars(items, vtype=GRB.BINARY, name="x")

    model.setObjective(
        gp.quicksum(values[i] * x[i] for i in items),
        GRB.MAXIMIZE,
    )

    model.addConstr(
        gp.quicksum(weights[i] * x[i] for i in items) <= capacity,
        name="storage_capacity",
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}

    return {"objective": None, "status": "not_optimal"}