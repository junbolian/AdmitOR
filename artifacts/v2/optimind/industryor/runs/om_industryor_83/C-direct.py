import gurobipy as gp
from gurobipy import GRB


def solve(params):
    machine_minutes_X = params["machine_minutes_X"]
    craftsman_minutes_X = params["craftsman_minutes_X"]
    machine_minutes_Y = params["machine_minutes_Y"]
    craftsman_minutes_Y = params["craftsman_minutes_Y"]
    machine_hours_capacity = params["machine_hours_capacity"]
    craftsman_hours_capacity = params["craftsman_hours_capacity"]
    machine_cost_per_hour = params["machine_cost_per_hour"]
    craftsman_cost_per_hour = params["craftsman_cost_per_hour"]
    revenue_X = params["revenue_X"]
    revenue_Y = params["revenue_Y"]
    contract_min_X = params["contract_min_X"]

    # Convert capacity from hours to minutes
    machine_minutes_capacity = machine_hours_capacity * 60
    craftsman_minutes_capacity = craftsman_hours_capacity * 60

    # Cost per minute (convert from per hour)
    machine_cost_per_minute = machine_cost_per_hour / 60
    craftsman_cost_per_minute = craftsman_cost_per_hour / 60

    model = gp.Model("production_planning")
    model.setParam("OutputFlag", 0)

    # Decision variables: integer units produced
    x = model.addVar(vtype=GRB.INTEGER, lb=0, name="X")
    y = model.addVar(vtype=GRB.INTEGER, lb=0, name="Y")

    # Objective: maximize profit = revenue - resource costs
    # Resource costs are based on time actually used
    profit_X = revenue_X - (machine_minutes_X * machine_cost_per_minute + craftsman_minutes_X * craftsman_cost_per_minute)
    profit_Y = revenue_Y - (machine_minutes_Y * machine_cost_per_minute + craftsman_minutes_Y * craftsman_cost_per_minute)

    model.setObjective(profit_X * x + profit_Y * y, GRB.MAXIMIZE)

    # Constraints
    model.addConstr(machine_minutes_X * x + machine_minutes_Y * y <= machine_minutes_capacity, name="machine_capacity")
    model.addConstr(craftsman_minutes_X * x + craftsman_minutes_Y * y <= craftsman_minutes_capacity, name="craftsman_capacity")
    model.addConstr(x >= contract_min_X, name="contract_min_X")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}