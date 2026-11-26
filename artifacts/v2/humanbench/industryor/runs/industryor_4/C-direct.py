import gurobipy as gp
from gurobipy import GRB

def solve(params):
    salary_A = params["salary_A"]
    salary_B = params["salary_B"]
    salary_C = params["salary_C"]
    salary_D = params["salary_D"]
    salary_E = params["salary_E"]
    max_hires = params["max_hires"]
    min_hires = params["min_hires"]
    budget = params["budget"]
    experience_A = params["experience_A"]
    experience_B = params["experience_B"]
    experience_C = params["experience_C"]
    experience_D = params["experience_D"]
    experience_E = params["experience_E"]
    min_experience = params["min_experience"]
    AE_max = params["AE_max"]
    min_advanced_degree = params["min_advanced_degree"]

    model = gp.Model("hiring")
    model.setParam("OutputFlag", 0)

    # Binary decision variables: hire each candidate or not
    x_A = model.addVar(vtype=GRB.BINARY, name="x_A")
    x_B = model.addVar(vtype=GRB.BINARY, name="x_B")
    x_C = model.addVar(vtype=GRB.BINARY, name="x_C")
    x_D = model.addVar(vtype=GRB.BINARY, name="x_D")
    x_E = model.addVar(vtype=GRB.BINARY, name="x_E")

    # Objective: minimize total salary
    model.setObjective(
        salary_A * x_A + salary_B * x_B + salary_C * x_C + salary_D * x_D + salary_E * x_E,
        GRB.MINIMIZE
    )

    # Maximum number of hires
    model.addConstr(x_A + x_B + x_C + x_D + x_E <= max_hires, name="max_hires")

    # Minimum number of hires
    model.addConstr(x_A + x_B + x_C + x_D + x_E >= min_hires, name="min_hires")

    # Budget constraint
    model.addConstr(
        salary_A * x_A + salary_B * x_B + salary_C * x_C + salary_D * x_D + salary_E * x_E <= budget,
        name="budget"
    )

    # Minimum total work experience
    model.addConstr(
        experience_A * x_A + experience_B * x_B + experience_C * x_C + experience_D * x_D + experience_E * x_E >= min_experience,
        name="min_experience"
    )

    # At most AE_max candidates from {A, E}
    model.addConstr(x_A + x_E <= AE_max, name="AE_max")

    # Minimum number of candidates with master's or PhD (B or C)
    model.addConstr(x_B + x_C >= min_advanced_degree, name="min_advanced_degree")

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver status {status}"}