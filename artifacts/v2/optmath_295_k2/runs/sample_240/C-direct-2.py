import gurobipy as gp
from gurobipy import GRB

def solve(params):
    values = params["values"]
    weights = params["weights"]
    capacity = params["capacity"]

    n = 27
    items = [f"item_{i}" for i in range(n)]

    model = gp.Model("knapsack")
    model.setParam("OutputFlag", 0)

    x = model.addVars(items, vtype=GRB.BINARY, name="x")

    if isinstance(values, dict):
        val = {item: values[item] for item in items}
        wt = {item: weights[item] for item in items}
    else:
        val = {item: values[i] for i, item in enumerate(items)}
        wt = {item: weights[i] for i, item in enumerate(items)}

    model.setObjective(gp.quicksum(val[item] * x[item] for item in items), GRB.MAXIMIZE)

    model.addConstr(
        gp.quicksum(wt[item] * x[item] for item in items) <= capacity,
        name="capacity"
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}