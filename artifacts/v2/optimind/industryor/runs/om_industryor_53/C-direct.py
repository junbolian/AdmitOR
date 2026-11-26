import gurobipy as gp
from gurobipy import GRB

def solve(params):
    math_req = params["math_requirement"]
    or_req = params["or_requirement"]
    cs_req = params["cs_requirement"]
    num_courses = params["num_courses"]

    # Courses: 0=Calculus, 1=Operations Research, 2=Data Structures,
    #          3=Management Statistics, 4=Computer Simulation,
    #          5=Computer Programming, 6=Forecasting
    courses = list(range(num_courses))

    # Category memberships
    math_courses = [0, 1, 2, 3, 6]       # Calculus, OR, DS, MgmtStat, Forecasting
    or_courses   = [1, 3, 4, 6]           # OR, MgmtStat, CompSim, Forecasting
    cs_courses   = [2, 4, 5]              # DS, CompSim, CompProg

    model = gp.Model("course_selection")
    model.setParam("OutputFlag", 0)

    # Binary variable: x[i] = 1 if course i is taken
    x = model.addVars(courses, vtype=GRB.BINARY, name="x")

    # Objective: minimize total courses taken
    model.setObjective(gp.quicksum(x[i] for i in courses), GRB.MINIMIZE)

    # Category requirements
    model.addConstr(gp.quicksum(x[i] for i in math_courses) >= math_req, "math_req")
    model.addConstr(gp.quicksum(x[i] for i in or_courses)   >= or_req,   "or_req")
    model.addConstr(gp.quicksum(x[i] for i in cs_courses)   >= cs_req,   "cs_req")

    # Prerequisites:
    # Computer Simulation (4) requires Computer Programming (5): x[4] <= x[5]
    model.addConstr(x[4] <= x[5], "prereq_compsim")
    # Data Structures (2) requires Computer Programming (5): x[2] <= x[5]
    model.addConstr(x[2] <= x[5], "prereq_ds")
    # Management Statistics (3) requires Calculus (0): x[3] <= x[0]
    model.addConstr(x[3] <= x[0], "prereq_mgmtstat")
    # Forecasting (6) requires Management Statistics (3): x[6] <= x[3]
    model.addConstr(x[6] <= x[3], "prereq_forecasting")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": float(model.ObjVal), "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}