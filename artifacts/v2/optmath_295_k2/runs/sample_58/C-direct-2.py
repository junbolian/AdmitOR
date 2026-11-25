import gurobipy as gp
from gurobipy import GRB


def solve(params):
    capacity = params["capacity"]
    item_values = params["item_values"]
    item_weights = params["item_weights"]

    n_items = len(item_values)

    model = gp.Model("knapsack")
    model.Params.OutputFlag = 0

    x = model.addVars(n_items, vtype=GRB.BINARY, name="x")

    model.setObjective(
        gp.quicksum(item_values[i] * x[i] for i in range(n_items)),
        GRB.MAXIMIZE,
    )

    model.addConstr(
        gp.quicksum(item_weights[i] * x[i] for i in range(n_items)) <= capacity,
        name="capacity",
    )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.status}"}