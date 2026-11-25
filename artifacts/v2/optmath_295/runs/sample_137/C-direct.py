import gurobipy as gp
from gurobipy import GRB


def solve(params):
    profit = params["profit"]
    stage_time_available = params["stage_time_available"]
    time_per_unit = params["time_per_unit"]
    lower_bound = params["lower_bound"]
    upper_bound = params["upper_bound"]

    num_products = 6
    num_stages = 11

    model = gp.Model("production_planning")

    x = model.addVars(num_products, lb=0.0, ub=GRB.INFINITY, vtype=GRB.CONTINUOUS, name="x")

    for i in range(num_products):
        x[i].lb = lower_bound[i]
        x[i].ub = upper_bound[i]

    model.setObjective(
        gp.quicksum(profit[i] * x[i] for i in range(num_products)),
        GRB.MAXIMIZE,
    )

    for s in range(num_stages):
        model.addConstr(
            gp.quicksum(time_per_unit[s][i] * x[i] for i in range(num_products))
            <= stage_time_available[s],
            name=f"stage_{s}",
        )

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    else:
        return {"objective": None, "status": "failed"}