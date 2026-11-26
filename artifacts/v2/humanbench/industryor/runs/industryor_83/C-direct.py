import gurobipy as gp
from gurobipy import GRB


def solve(params):
    C0 = float(params["initial_capital"])
    r1 = float(params["rate_project1"])            # annual profit rate, project 1
    m2 = float(params["multiplier_project2"])      # principal+interest multiplier, project 2
    cap2 = float(params["cap_project2"])
    m3 = float(params["multiplier_project3"])      # principal+interest multiplier, project 3
    cap3 = float(params["cap_project3"])
    m4 = float(params["multiplier_project4"])      # principal+interest multiplier, project 4
    cap4 = float(params["cap_project4"])

    model = gp.Model("investment")
    model.Params.OutputFlag = 0

    # Project 1 (reinvestable each year): amount invested at start of year t
    x1_1 = model.addVar(lb=0.0, name="x1_y1")
    x1_2 = model.addVar(lb=0.0, name="x1_y2")
    x1_3 = model.addVar(lb=0.0, name="x1_y3")

    # Project 2: invest at start of year 1, recovered end of year 2
    x2 = model.addVar(lb=0.0, ub=cap2, name="x_p2")
    # Project 3: invest at start of year 2, recovered end of year 3
    x3 = model.addVar(lb=0.0, ub=cap3, name="x_p3")
    # Project 4: invest at start of year 3, recovered within one year
    x4 = model.addVar(lb=0.0, ub=cap4, name="x_p4")

    # Idle cash carried from year t to year t+1 (uninvested funds)
    cash1 = model.addVar(lb=0.0, name="cash_y1")
    cash2 = model.addVar(lb=0.0, name="cash_y2")
    cash3 = model.addVar(lb=0.0, name="cash_y3")

    # Year 1: allocate initial capital
    model.addConstr(x1_1 + x2 + cash1 == C0)

    # Year 2: available = project-1 return + idle cash from year 1
    model.addConstr(x1_2 + x3 + cash2 == (1.0 + r1) * x1_1 + cash1)

    # Year 3: available = project-1 return + project-2 recovery + idle cash
    model.addConstr(x1_3 + x4 + cash3 == (1.0 + r1) * x1_2 + m2 * x2 + cash2)

    # End of year 3 wealth
    wealth = (1.0 + r1) * x1_3 + m4 * x4 + cash3
    model.setObjective(wealth, GRB.MAXIMIZE)

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    if model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    if model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    return {"objective": None, "status": "failed"}