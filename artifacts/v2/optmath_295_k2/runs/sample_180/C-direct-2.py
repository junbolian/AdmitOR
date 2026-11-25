import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit = params["profit"]
    stage_capacity = params["stage_capacity"]
    min_commitment = params["min_commitment"]
    market_demand = params["market_demand"]
    stage_time = params["stage_time"]

    num_products = 6
    num_stages = 11

    model = gp.Model("production_planning")
    model.setParam("OutputFlag", 0)

    x = model.addVars(num_products, lb=0.0, name="x")

    model.setObjective(
        gp.quicksum(profit[p] * x[p] for p in range(num_products)),
        GRB.MAXIMIZE
    )

    for s in range(num_stages):
        model.addConstr(
            gp.quicksum(stage_time[s][p] * x[p] for p in range(num_products)) <= stage_capacity[s],
            name=f"stage_{s}"
        )

    for p in range(num_products):
        model.addConstr(x[p] >= min_commitment[p], name=f"min_commit_{p}")
        model.addConstr(x[p] <= market_demand[p], name=f"market_demand_{p}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}