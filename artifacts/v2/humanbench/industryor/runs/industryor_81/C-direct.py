import gurobipy as gp
from gurobipy import GRB

def solve(params):
    initial_capital = params["initial_capital"]
    annual_reinvest_profit_rate = params["annual_reinvest_profit_rate"]
    project2_total_interest_rate = params["project2_total_interest_rate"]
    project2_investment_cap = params["project2_investment_cap"]
    project3_total_interest_rate = params["project3_total_interest_rate"]
    project3_investment_cap = params["project3_investment_cap"]
    project4_profit_rate = params["project4_profit_rate"]
    project4_investment_cap = params["project4_investment_cap"]

    model = gp.Model("investment")
    model.setParam("OutputFlag", 0)

    # Decision variables:
    # x1_t: amount invested in project 1 at beginning of year t (t=1,2,3)
    # x2: amount invested in project 2 at beginning of year 1
    # x3: amount invested in project 3 at beginning of year 2
    # x4: amount invested in project 4 at beginning of year 3

    x1_1 = model.addVar(lb=0, name="x1_1")
    x1_2 = model.addVar(lb=0, name="x1_2")
    x1_3 = model.addVar(lb=0, name="x1_3")
    x2   = model.addVar(lb=0, ub=project2_investment_cap, name="x2")
    x3   = model.addVar(lb=0, ub=project3_investment_cap, name="x3")
    x4   = model.addVar(lb=0, ub=project4_investment_cap, name="x4")

    # Year 1 budget constraint:
    # x1_1 + x2 <= initial_capital
    model.addConstr(x1_1 + x2 <= initial_capital, name="budget_year1")

    # Year 2 budget constraint:
    # At the end of year 1, project 1 investment from year 1 returns principal + profit.
    # Available at start of year 2 = x1_1 * (1 + annual_reinvest_profit_rate)
    # Invest in x1_2 and x3
    model.addConstr(
        x1_2 + x3 <= x1_1 * (1 + annual_reinvest_profit_rate),
        name="budget_year2"
    )

    # Year 3 budget constraint:
    # At start of year 3, available funds come from:
    #   - project 1 year 2 returns: x1_2 * (1 + annual_reinvest_profit_rate)
    #   - project 2 recovery at end of year 2: x2 * (1 + project2_total_interest_rate)
    #   - project 3 recovery at end of year 2: x3 * (1 + project3_total_interest_rate)
    # Invest in x1_3 and x4
    model.addConstr(
        x1_3 + x4 <= (x1_2 * (1 + annual_reinvest_profit_rate)
                      + x2 * (1 + project2_total_interest_rate)
                      + x3 * (1 + project3_total_interest_rate)),
        name="budget_year3"
    )

    # Objective: maximize total capital at end of year 3
    # = project 1 year 3 returns + project 4 returns
    obj = (x1_3 * (1 + annual_reinvest_profit_rate)
           + x4 * (1 + project4_profit_rate))
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