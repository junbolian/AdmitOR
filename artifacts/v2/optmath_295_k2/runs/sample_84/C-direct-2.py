import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit = params["profit"]
    time_per_unit = params["time_per_unit"]
    total_time = params["total_time"]
    min_production = params["min_production"]
    max_production = params["max_production"]

    n_products = 10

    model = gp.Model()
    model.setParam("OutputFlag", 0)

    x = model.addVars(n_products, lb=0.0, name="x")

    for i in range(n_products):
        x[i].lb = min_production[i]
        x[i].ub = max_production[i]

    model.setObjective(
        gp.quicksum(profit[i] * x[i] for i in range(n_products)),
        GRB.MAXIMIZE
    )

    model.addConstr(
        gp.quicksum(time_per_unit[i] * x[i] for i in range(n_products)) <= total_time,
        name="time_limit"
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