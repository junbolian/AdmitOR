import gurobipy as gp
from gurobipy import GRB


def solve(params):
    values = [
        params["value_item0"],
        params["value_item1"],
        params["value_item2"],
    ]
    weights = [
        params["weight_item0"],
        params["weight_item1"],
        params["weight_item2"],
    ]
    capacity = params["capacity"]

    model = gp.Model("shipment")
    model.Params.OutputFlag = 0

    x = model.addVars(3, vtype=GRB.BINARY, name="x")

    model.setObjective(
        gp.quicksum(values[i] * x[i] for i in range(3)),
        sense=GRB.MAXIMIZE,
    )

    model.addConstr(
        gp.quicksum(weights[i] * x[i] for i in range(3)) <= capacity,
        name="capacity",
    )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    else:
        return {"objective": None, "status": f"gurobi_status_{model.status}"}