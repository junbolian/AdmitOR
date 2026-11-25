import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit_per_unit = params["profit_per_unit"]
    stage_hours_available = params["stage_hours_available"]
    stage_time_per_unit = params["stage_time_per_unit"]
    min_production = params["min_production"]
    max_demand = params["max_demand"]

    num_products = 6
    num_stages = 12

    model = gp.Model("production_planning")
    model.setParam("OutputFlag", 0)

    x = model.addVars(num_products, lb=0.0, name="x")

    model.setObjective(
        gp.quicksum(profit_per_unit[j] * x[j] for j in range(num_products)),
        GRB.MAXIMIZE
    )

    for i in range(num_stages):
        model.addConstr(
            gp.quicksum(stage_time_per_unit[i][j] * x[j] for j in range(num_products))
            <= stage_hours_available[i],
            name=f"stage_{i}"
        )

    for j in range(num_products):
        model.addConstr(x[j] >= min_production[j], name=f"min_prod_{j}")
        model.addConstr(x[j] <= max_demand[j], name=f"max_demand_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}