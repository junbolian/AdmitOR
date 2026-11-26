import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit_A = params["profit_A"]
    profit_B = params["profit_B"]
    assembly_time_A = params["assembly_time_A"]  # minutes
    assembly_time_B = params["assembly_time_B"]  # minutes
    weekly_machine_hours = params["weekly_machine_hours"]  # hours
    ratio_A_per_5 = params["ratio_A_per_5"]  # units of A per ratio block
    ratio_B_min = params["ratio_B_min"]      # minimum units of B per ratio block

    weekly_machine_minutes = weekly_machine_hours * 60

    model = gp.Model("production_planning")
    model.setParam("OutputFlag", 0)

    x_A = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name="x_A")
    x_B = model.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name="x_B")

    model.setObjective(profit_A * x_A + profit_B * x_B, GRB.MAXIMIZE)

    # Machine time constraint (convert hours to minutes)
    model.addConstr(
        assembly_time_A * x_A + assembly_time_B * x_B <= weekly_machine_minutes,
        name="machine_time"
    )

    # Technical ratio constraint: for every ratio_A_per_5 units of A, at least ratio_B_min units of B
    # i.e. x_B / x_A >= ratio_B_min / ratio_A_per_5
    # rewritten: ratio_A_per_5 * x_B >= ratio_B_min * x_A
    model.addConstr(
        ratio_A_per_5 * x_B >= ratio_B_min * x_A,
        name="technical_ratio"
    )

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}