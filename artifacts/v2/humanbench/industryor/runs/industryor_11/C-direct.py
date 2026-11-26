import gurobipy as gp
from gurobipy import GRB

def solve(params):
    labor_hours_advanced = params["labor_hours_advanced"]
    inspection_hours_advanced = params["inspection_hours_advanced"]
    profit_advanced = params["profit_advanced"]

    labor_hours_intermediate = params["labor_hours_intermediate"]
    inspection_hours_intermediate = params["inspection_hours_intermediate"]
    profit_intermediate = params["profit_intermediate"]

    labor_hours_basic = params["labor_hours_basic"]
    inspection_hours_basic = params["inspection_hours_basic"]
    profit_basic = params["profit_basic"]

    labor_capacity = params["labor_capacity"]
    inspection_capacity = params["inspection_capacity"]

    demand_advanced = params["demand_advanced"]
    demand_intermediate = params["demand_intermediate"]
    demand_basic = params["demand_basic"]

    model = gp.Model("toy_production")
    model.setParam("OutputFlag", 0)

    x_advanced = model.addVar(lb=0, vtype=GRB.CONTINUOUS, name="x_advanced")
    x_intermediate = model.addVar(lb=0, vtype=GRB.CONTINUOUS, name="x_intermediate")
    x_basic = model.addVar(lb=0, vtype=GRB.CONTINUOUS, name="x_basic")

    model.setObjective(
        profit_advanced * x_advanced + profit_intermediate * x_intermediate + profit_basic * x_basic,
        GRB.MAXIMIZE
    )

    model.addConstr(
        labor_hours_advanced * x_advanced + labor_hours_intermediate * x_intermediate + labor_hours_basic * x_basic <= labor_capacity,
        name="labor_constraint"
    )
    model.addConstr(
        inspection_hours_advanced * x_advanced + inspection_hours_intermediate * x_intermediate + inspection_hours_basic * x_basic <= inspection_capacity,
        name="inspection_constraint"
    )

    model.addConstr(x_advanced <= demand_advanced, name="demand_advanced_constraint")
    model.addConstr(x_intermediate <= demand_intermediate, name="demand_intermediate_constraint")
    model.addConstr(x_basic <= demand_basic, name="demand_basic_constraint")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}