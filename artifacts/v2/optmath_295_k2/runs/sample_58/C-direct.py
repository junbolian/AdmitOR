import gurobipy as gp
from gurobipy import GRB

def solve(params):
    capacity = params["capacity"]
    item_values = params["item_values"]
    item_weights = params["item_weights"]

    n_items = len(item_values)
    items = range(n_items)

    model = gp.Model("knapsack")
    model.setParam("OutputFlag", 0)

    x = model.addVars(items, vtype=GRB.BINARY, name="x")

    model.setObjective(
        gp.quicksum(item_values[i] * x[i] for i in items),
        GRB.MAXIMIZE
    )

    model.addConstr(
        gp.quicksum(item_weights[i] * x[i] for i in items) <= capacity,
        name="weight_capacity"
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}