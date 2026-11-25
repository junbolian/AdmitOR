import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit = {
        (1, 1): params["profit_p1_s1"],
        (2, 1): params["profit_p2_s1"],
        (3, 1): params["profit_p3_s1"],
        (1, 2): params["profit_p1_s2"],
        (2, 2): params["profit_p2_s2"],
        (3, 2): params["profit_p3_s2"],
        (1, 3): params["profit_p1_s3"],
        (2, 3): params["profit_p2_s3"],
        (3, 3): params["profit_p3_s3"],
        (1, 4): params["profit_p1_s4"],
        (2, 4): params["profit_p2_s4"],
        (3, 4): params["profit_p3_s4"],
    }

    demand = {
        (1, 1): params["demand_p1_s1"],
        (2, 1): params["demand_p2_s1"],
        (3, 1): params["demand_p3_s1"],
        (1, 2): params["demand_p1_s2"],
        (2, 2): params["demand_p2_s2"],
        (3, 2): params["demand_p3_s2"],
        (1, 3): params["demand_p1_s3"],
        (2, 3): params["demand_p2_s3"],
        (3, 3): params["demand_p3_s3"],
        (1, 4): params["demand_p1_s4"],
        (2, 4): params["demand_p2_s4"],
        (3, 4): params["demand_p3_s4"],
    }

    products = [1, 2, 3]
    schools = [1, 2, 3, 4]

    model = gp.Model("school_supply")
    model.setParam("OutputFlag", 0)

    x = {}
    for p in products:
        for s in schools:
            x[p, s] = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name=f"x_p{p}_s{s}")

    model.setObjective(
        gp.quicksum(profit[p, s] * x[p, s] for p in products for s in schools),
        GRB.MAXIMIZE
    )

    for p in products:
        for s in schools:
            model.addConstr(x[p, s] == demand[p, s], name=f"demand_p{p}_s{s}")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}