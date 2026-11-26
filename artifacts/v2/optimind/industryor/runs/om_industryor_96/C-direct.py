import gurobipy as gp
from gurobipy import GRB

def solve(params):
    profit_A = params["profit_A"]
    profit_B = params["profit_B"]
    steel_A = params["steel_A"]
    steel_B = params["steel_B"]
    aluminum_A = params["aluminum_A"]
    aluminum_B = params["aluminum_B"]
    labor_A = params["labor_A"]
    labor_B = params["labor_B"]
    steel_capacity = params["steel_capacity"]
    aluminum_capacity = params["aluminum_capacity"]
    labor_capacity = params["labor_capacity"]
    overtime_pay = params["overtime_pay"]

    model = gp.Model("production_plan")
    model.setParam("OutputFlag", 0)

    # Decision variables
    x_A = model.addVar(vtype=GRB.INTEGER, lb=0, name="x_A")  # units of product A
    x_B = model.addVar(vtype=GRB.INTEGER, lb=0, name="x_B")  # units of product B
    overtime = model.addVar(vtype=GRB.CONTINUOUS, lb=0, name="overtime")  # overtime hours

    # Objective: maximize profit minus overtime cost
    model.setObjective(
        profit_A * x_A + profit_B * x_B - overtime_pay * overtime,
        GRB.MAXIMIZE
    )

    # Resource constraints
    model.addConstr(steel_A * x_A + steel_B * x_B <= steel_capacity, name="steel")
    model.addConstr(aluminum_A * x_A + aluminum_B * x_B <= aluminum_capacity, name="aluminum")

    # Labor constraint: total labor = regular + overtime
    model.addConstr(labor_A * x_A + labor_B * x_B <= labor_capacity + overtime, name="labor")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}