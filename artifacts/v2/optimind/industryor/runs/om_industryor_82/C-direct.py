import gurobipy as gp
from gurobipy import GRB

def solve(params):
    salary_A = params["salary_A"]
    salary_B = params["salary_B"]
    salary_C = params["salary_C"]
    salary_D = params["salary_D"]
    salary_E = params["salary_E"]
    max_hires = params["max_hires"]
    budget = params["budget"]
    min_hires = params["min_hires"]
    experience_A = params["experience_A"]
    experience_B = params["experience_B"]
    experience_C = params["experience_C"]
    experience_D = params["experience_D"]
    experience_E = params["experience_E"]
    min_experience = params["min_experience"]
    max_from_A_E = params["max_from_A_E"]
    min_advanced_degree = params["min_advanced_degree"]

    model = gp.Model("recruitment")
    model.setParam("OutputFlag", 0)

    # Binary decision variables: hire each candidate or not
    xA = model.addVar(vtype=GRB.BINARY, name="xA")
    xB = model.addVar(vtype=GRB.BINARY, name="xB")
    xC = model.addVar(vtype=GRB.BINARY, name="xC")
    xD = model.addVar(vtype=GRB.BINARY, name="xD")
    xE = model.addVar(vtype=GRB.BINARY, name="xE")

    # Objective: minimize total salary paid
    model.setObjective(
        salary_A * xA + salary_B * xB + salary_C * xC + salary_D * xD + salary_E * xE,
        GRB.MINIMIZE
    )

    # Budget constraint
    model.addConstr(
        salary_A * xA + salary_B * xB + salary_C * xC + salary_D * xD + salary_E * xE <= budget,
        name="budget"
    )

    # Maximum hires
    model.addConstr(xA + xB + xC + xD + xE <= max_hires, name="max_hires")

    # Minimum hires
    model.addConstr(xA + xB + xC + xD + xE >= min_hires, name="min_hires")

    # Minimum total experience
    model.addConstr(
        experience_A * xA + experience_B * xB + experience_C * xC + experience_D * xD + experience_E * xE >= min_experience,
        name="min_experience"
    )

    # At most max_from_A_E from candidates A and E (equivalent skills)
    model.addConstr(xA + xE <= max_from_A_E, name="max_from_A_E")

    # At least min_advanced_degree candidates with Master's or Doctoral degree (B or C)
    model.addConstr(xB + xC >= min_advanced_degree, name="min_advanced_degree")

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{status}"}