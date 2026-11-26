import gurobipy as gp
from gurobipy import GRB

def solve(params):
    required_math = params["required_math_courses"]
    required_or = params["required_or_courses"]
    required_computer = params["required_computer_courses"]

    # Courses: 0=calculus, 1=operations_research, 2=data_structures,
    #          3=management_statistics, 4=computer_simulation,
    #          5=computer_programming, 6=forecasting
    courses = list(range(7))

    # Category memberships (course contributes credits to each listed category)
    # math credits
    math_courses = [0, 1, 2, 3, 6]        # calculus, OR, data_structures, mgmt_stat, forecasting
    # OR credits
    or_courses = [1, 3, 4, 6]             # OR, mgmt_stat, comp_sim, forecasting
    # computer credits
    computer_courses = [2, 4, 5]          # data_structures, comp_sim, comp_programming

    model = gp.Model("course_selection")
    model.setParam("OutputFlag", 0)

    # Binary variable: take course i or not
    x = model.addVars(courses, vtype=GRB.BINARY, name="x")

    # Objective: minimize total number of courses taken
    model.setObjective(gp.quicksum(x[i] for i in courses), GRB.MINIMIZE)

    # Category requirements
    model.addConstr(gp.quicksum(x[i] for i in math_courses) >= required_math, "math_req")
    model.addConstr(gp.quicksum(x[i] for i in or_courses) >= required_or, "or_req")
    model.addConstr(gp.quicksum(x[i] for i in computer_courses) >= required_computer, "computer_req")

    # Prerequisite constraints:
    # computer_simulation (4) requires computer_programming (5): x[4] <= x[5]
    model.addConstr(x[4] <= x[5], "prereq_comp_sim")
    # data_structures (2) requires computer_programming (5): x[2] <= x[5]
    model.addConstr(x[2] <= x[5], "prereq_data_struct")
    # management_statistics (3) requires calculus (0): x[3] <= x[0]
    model.addConstr(x[3] <= x[0], "prereq_mgmt_stat")
    # forecasting (6) requires management_statistics (3): x[6] <= x[3]
    model.addConstr(x[6] <= x[3], "prereq_forecasting")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}