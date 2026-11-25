import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit = params["profit"]
    time_per_unit = params["time_per_unit"]
    capacity_hours = params["capacity_hours"]
    min_production = params["min_production"]
    max_production = params["max_production"]

    n = len(profit)

    model = gp.Model("production_planning")
    model.Params.OutputFlag = 0

    x = model.addVars(n, lb=0.0, name="prod")

    model.setObjective(
        gp.quicksum(profit[i] * x[i] for i in range(n)),
        GRB.MAXIMIZE,
    )

    model.addConstr(
        gp.quicksum(time_per_unit[i] * x[i] for i in range(n)) <= capacity_hours,
        name="capacity",
    )

    for i in range(n):
        model.addConstr(x[i] >= min_production[i], name=f"min_{i}")
        model.addConstr(x[i] <= max_production[i], name=f"max_{i}")

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.status}"}