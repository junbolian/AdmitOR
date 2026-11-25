import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit_per_unit = params["profit_per_unit"]
    stage_hours = params["stage_hours"]
    time_coeffs = params["time_coeffs"]
    min_production = params["min_production"]
    max_demand = params["max_demand"]

    num_products = 6
    num_stages = 11

    model = gp.Model("production_planning")
    model.setParam("OutputFlag", 0)

    x = model.addVars(num_products, lb=0.0, name="x")

    model.setObjective(
        gp.quicksum(profit_per_unit[p] * x[p] for p in range(num_products)),
        GRB.MAXIMIZE
    )

    for s in range(num_stages):
        model.addConstr(
            gp.quicksum(time_coeffs[s][p] * x[p] for p in range(num_products)) <= stage_hours[s],
            name=f"stage_{s}"
        )

    for p in range(num_products):
        model.addConstr(x[p] >= min_production[p], name=f"min_prod_{p}")
        model.addConstr(x[p] <= max_demand[p], name=f"max_demand_{p}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}