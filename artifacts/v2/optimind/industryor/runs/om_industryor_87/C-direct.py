import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit_A = params["profit_A"]
    profit_B = params["profit_B"]
    hours_available = params["hours_available"]
    hours_per_A = params["hours_per_A"]
    hours_per_B = params["hours_per_B"]
    demand_ratio_B_to_A = params["demand_ratio_B_to_A"]
    space_per_A = params["space_per_A"]
    space_per_B = params["space_per_B"]
    storage_capacity = params["storage_capacity"]

    model = gp.Model("production_planning")
    model.setParam("OutputFlag", 0)

    # Decision variables: integer units of A and B produced
    x_A = model.addVar(vtype=GRB.INTEGER, lb=0, name="x_A")
    x_B = model.addVar(vtype=GRB.INTEGER, lb=0, name="x_B")

    # Objective: maximize total profit
    model.setObjective(profit_A * x_A + profit_B * x_B, GRB.MAXIMIZE)

    # Production hours constraint
    model.addConstr(hours_per_A * x_A + hours_per_B * x_B <= hours_available, name="hours")

    # Demand ratio constraint: B >= demand_ratio_B_to_A * A
    model.addConstr(x_B >= demand_ratio_B_to_A * x_A, name="demand_ratio")

    # Storage capacity constraint: space_per_A * x_A + space_per_B * x_B <= storage_capacity
    model.addConstr(space_per_A * x_A + space_per_B * x_B <= storage_capacity, name="storage")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}