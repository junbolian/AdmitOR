import gurobipy as gp
from gurobipy import GRB


def solve(params):
    profit = params["profit"]
    time_per_unit = params["time_per_unit"]
    total_time = params["total_time"]
    min_production = params["min_production"]
    max_production = params["max_production"]

    n = len(profit)

    model = gp.Model("production")
    model.Params.OutputFlag = 0

    x = model.addVars(n, lb=0, name="x")

    model.setObjective(
        gp.quicksum(profit[i] * x[i] for i in range(n)),
        GRB.MAXIMIZE,
    )

    model.addConstr(
        gp.quicksum(time_per_unit[i] * x[i] for i in range(n)) <= total_time,
        "total_time",
    )

    for i in range(n):
        model.addConstr(x[i] >= min_production[i], f"min_prod_{i}")
        model.addConstr(x[i] <= max_production[i], f"max_prod_{i}")

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    else:
        return {"objective": None, "status": f"status_{model.status}"}