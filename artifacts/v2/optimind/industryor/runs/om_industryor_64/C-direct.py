import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit_high = params["profit_high"]
    profit_mid = params["profit_mid"]
    profit_low = params["profit_low"]
    labor_high = params["labor_high"]
    labor_mid = params["labor_mid"]
    labor_low = params["labor_low"]
    inspect_high = params["inspect_high"]
    inspect_mid = params["inspect_mid"]
    inspect_low = params["inspect_low"]
    labor_capacity = params["labor_capacity"]
    inspection_capacity = params["inspection_capacity"]
    demand_high = params["demand_high"]
    demand_mid = params["demand_mid"]
    demand_low = params["demand_low"]

    model = gp.Model("tabletop_golf")
    model.setParam("OutputFlag", 0)

    x_high = model.addVar(lb=0, vtype=GRB.INTEGER, name="x_high")
    x_mid = model.addVar(lb=0, vtype=GRB.INTEGER, name="x_mid")
    x_low = model.addVar(lb=0, vtype=GRB.INTEGER, name="x_low")

    model.setObjective(
        profit_high * x_high + profit_mid * x_mid + profit_low * x_low,
        GRB.MAXIMIZE
    )

    model.addConstr(
        labor_high * x_high + labor_mid * x_mid + labor_low * x_low <= labor_capacity,
        name="labor"
    )
    model.addConstr(
        inspect_high * x_high + inspect_mid * x_mid + inspect_low * x_low <= inspection_capacity,
        name="inspection"
    )
    model.addConstr(x_high <= demand_high, name="demand_high")
    model.addConstr(x_mid <= demand_mid, name="demand_mid")
    model.addConstr(x_low <= demand_low, name="demand_low")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}