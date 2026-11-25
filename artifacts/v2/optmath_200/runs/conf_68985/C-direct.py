import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit = params["profit"]
    stage_hours = params["stage_hours"]
    time_coeff = params["time_coeff"]
    min_commitment = params["min_commitment"]
    demand_limit = params["demand_limit"]

    num_products = 6
    num_stages = 11

    model = gp.Model("production_planning")
    model.setParam("OutputFlag", 0)

    x = model.addVars(num_products, lb=0.0, name="x")

    model.setObjective(
        gp.quicksum(profit[j] * x[j] for j in range(num_products)),
        GRB.MAXIMIZE
    )

    for i in range(num_stages):
        model.addConstr(
            gp.quicksum(time_coeff[i * num_products + j] * x[j] for j in range(num_products)) <= stage_hours[i],
            name=f"stage_{i}"
        )

    for j in range(num_products):
        model.addConstr(x[j] >= min_commitment[j], name=f"min_commit_{j}")
        model.addConstr(x[j] <= demand_limit[j], name=f"demand_limit_{j}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}