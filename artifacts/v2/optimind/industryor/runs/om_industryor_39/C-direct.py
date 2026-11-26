import gurobipy as gp
from gurobipy import GRB

def solve(params):
    fund = params["fund"]
    project1_rate = params["project1_rate"]
    project2_return = params["project2_return"]
    project2_cap = params["project2_cap"]
    project3_return = params["project3_return"]
    project3_cap = params["project3_cap"]
    project4_return = params["project4_return"]
    project4_cap = params["project4_cap"]

    model = gp.Model("investment")
    model.setParam("OutputFlag", 0)

    # Decision variables
    # x1_t: amount invested in project 1 at start of year t (t=1,2,3)
    x1_1 = model.addVar(lb=0, name="x1_1")
    x1_2 = model.addVar(lb=0, name="x1_2")
    x1_3 = model.addVar(lb=0, name="x1_3")

    # x2: amount invested in project 2 at start of year 1
    x2 = model.addVar(lb=0, ub=project2_cap, name="x2")

    # x3: amount invested in project 3 at start of year 2
    x3 = model.addVar(lb=0, ub=project3_cap, name="x3")

    # x4: amount invested in project 4 at start of year 3
    x4 = model.addVar(lb=0, ub=project4_cap, name="x4")

    # Slack variables representing uninvested cash carried forward each period
    slack_1 = model.addVar(lb=0, name="slack_1")
    slack_2 = model.addVar(lb=0, name="slack_2")
    slack_3 = model.addVar(lb=0, name="slack_3")

    # Year 1 start: total allocation equals available fund
    # Available: fund
    # Allocated to: project1 (year1), project2, and idle cash
    model.addConstr(
        x1_1 + x2 + slack_1 == fund,
        name="budget_year1"
    )

    # Year 2 start: funds available from project1 year1 return + idle cash from year1
    # Project 1 returns (1 + project1_rate) * x1_1 at end of year 1 (available start of year 2)
    # Project 2 recovers at END of year 2, not available at start of year 2
    # Idle cash slack_1 carries forward as-is
    model.addConstr(
        x1_2 + x3 + slack_2 == (1 + project1_rate) * x1_1 + slack_1,
        name="budget_year2"
    )

    # Year 3 start: funds available from:
    #   - project1 year2 return: (1 + project1_rate) * x1_2
    #   - project2 recovery at end of year 2: project2_return * x2
    #   - project3 recovery at end of year 2: project3_return * x3
    #   - idle cash from year 2: slack_2
    model.addConstr(
        x1_3 + x4 + slack_3 == (1 + project1_rate) * x1_2 + project2_return * x2 + project3_return * x3 + slack_2,
        name="budget_year3"
    )

    # Objective: total value at end of year 3
    #   - project1 year3 return: (1 + project1_rate) * x1_3
    #   - project4 return: project4_return * x4
    #   - uninvested cash: slack_3
    obj = (1 + project1_rate) * x1_3 + project4_return * x4 + slack_3

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