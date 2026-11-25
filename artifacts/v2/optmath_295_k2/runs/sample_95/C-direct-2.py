import gurobipy as gp
from gurobipy import GRB


def solve(params):
    n = 9
    values = [params[f"value_{i}"] for i in range(n)]
    weights = [params[f"weight_{i}"] for i in range(n)]
    capacity = params["capacity"]

    model = gp.Model("knapsack")
    model.Params.OutputFlag = 0

    x = model.addVars(n, vtype=GRB.BINARY, name="x")

    model.setObjective(
        gp.quicksum(values[i] * x[i] for i in range(n)),
        sense=GRB.MAXIMIZE,
    )

    model.addConstr(
        gp.quicksum(weights[i] * x[i] for i in range(n)) <= capacity,
        name="capacity",
    )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.status}"}