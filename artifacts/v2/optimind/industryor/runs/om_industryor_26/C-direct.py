import gurobipy as gp
from gurobipy import GRB

def solve(params):
    initial_fund = params["initial_fund"]
    return_rate_project1 = params["return_rate_project1"]
    return_multiplier_project2 = params["return_multiplier_project2"]
    cap_project2 = params["cap_project2"]
    return_multiplier_project3 = params["return_multiplier_project3"]
    cap_project3 = params["cap_project3"]
    return_multiplier_project4 = params["return_multiplier_project4"]
    cap_project4 = params["cap_project4"]

    # Decision variables:
    # x1_y1: amount invested in project 1 at beginning of year 1
    # x1_y2: amount invested in project 1 at beginning of year 2
    # x1_y3: amount invested in project 1 at beginning of year 3
    # x2:    amount invested in project 2 at beginning of year 1
    # x3:    amount invested in project 3 at beginning of year 2
    # x4:    amount invested in project 4 at beginning of year 3

    model = gp.Model("investment")
    model.setParam("OutputFlag", 0)

    x1_y1 = model.addVar(lb=0, name="x1_y1")
    x1_y2 = model.addVar(lb=0, name="x1_y2")
    x1_y3 = model.addVar(lb=0, name="x1_y3")
    x2    = model.addVar(lb=0, ub=cap_project2, name="x2")
    x3    = model.addVar(lb=0, ub=cap_project3, name="x3")
    x4    = model.addVar(lb=0, ub=cap_project4, name="x4")

    # project 1 principal+interest multiplier per year
    p1_multiplier = 1 + return_rate_project1

    # Year 1 budget constraint: x1_y1 + x2 <= initial_fund
    model.addConstr(x1_y1 + x2 <= initial_fund, name="budget_y1")

    # Year 2 budget constraint:
    # Available = principal+interest from project 1 year 1
    # x1_y2 + x3 <= p1_multiplier * x1_y1
    model.addConstr(x1_y2 + x3 <= p1_multiplier * x1_y1, name="budget_y2")

    # Year 3 budget constraint:
    # Available = principal+interest from project 1 year 2
    #           + principal+interest from project 2 (matures end of year 2)
    # x1_y3 + x4 <= p1_multiplier * x1_y2 + return_multiplier_project2 * x2
    model.addConstr(
        x1_y3 + x4 <= p1_multiplier * x1_y2 + return_multiplier_project2 * x2,
        name="budget_y3"
    )

    # Objective: total value at end of year 3
    # = principal+interest from project 1 year 3
    # + principal+interest from project 3 (invested at beginning of year 2, matures end of year 3)
    # + principal+interest from project 4
    obj = (p1_multiplier * x1_y3
           + return_multiplier_project3 * x3
           + return_multiplier_project4 * x4)

    model.setObjective(obj, GRB.MAXIMIZE)
    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}