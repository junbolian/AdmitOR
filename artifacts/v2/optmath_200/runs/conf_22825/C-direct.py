import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit_per_unit = params["profit_per_unit"]
    time_per_unit = params["time_per_unit"]
    total_capacity_hours = params["total_capacity_hours"]
    min_demand = params["min_demand"]
    max_demand = params["max_demand"]

    n_products = 10

    model = gp.Model("production_planning")
    model.setParam("OutputFlag", 0)

    x = model.addVars(n_products, lb=0.0, name="x")

    for i in range(n_products):
        x[i].lb = min_demand[i]
        x[i].ub = max_demand[i]

    model.setObjective(
        gp.quicksum(profit_per_unit[i] * x[i] for i in range(n_products)),
        GRB.MAXIMIZE
    )

    model.addConstr(
        gp.quicksum(time_per_unit[i] * x[i] for i in range(n_products)) <= total_capacity_hours,
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