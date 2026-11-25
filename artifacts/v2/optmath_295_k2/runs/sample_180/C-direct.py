import gurobipy as gp
from gurobipy import GRB


def solve(params):
    profit = params["profit"]
    stage_capacity = params["stage_capacity"]
    min_commitment = params["min_commitment"]
    market_demand = params["market_demand"]
    stage_time = params["stage_time"]

    num_products = len(profit)
    num_stages = len(stage_capacity)

    model = gp.Model("production_planning")
    model.Params.OutputFlag = 0

    x = model.addVars(num_products, lb=0.0, vtype=GRB.CONTINUOUS, name="x")

    model.setObjective(
        gp.quicksum(profit[i] * x[i] for i in range(num_products)),
        GRB.MAXIMIZE,
    )

    for s in range(num_stages):
        model.addConstr(
            gp.quicksum(stage_time[s][i] * x[i] for i in range(num_products))
            <= stage_capacity[s],
            name=f"stage_capacity_{s}",
        )

    for i in range(num_products):
        model.addConstr(x[i] >= min_commitment[i], name=f"min_commit_{i}")
        model.addConstr(x[i] <= market_demand[i], name=f"max_demand_{i}")

    model.optimize()

    if model.status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    if model.status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    return {"objective": None, "status": f"status_{model.status}"}