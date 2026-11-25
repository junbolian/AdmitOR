import gurobipy as gp
from gurobipy import GRB

def solve(params):
    values = params["values"]
    weights = params["weights"]
    capacity = params["capacity"]

    n = len(values)
    items = list(range(n))

    model = gp.Model("knapsack")
    model.setParam("OutputFlag", 0)

    x = model.addVars(items, vtype=GRB.BINARY, name="x")

    model.setObjective(gp.quicksum(values[i] * x[i] for i in items), GRB.MAXIMIZE)

    model.addConstr(gp.quicksum(weights[i] * x[i] for i in items) <= capacity, "weight_limit")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}