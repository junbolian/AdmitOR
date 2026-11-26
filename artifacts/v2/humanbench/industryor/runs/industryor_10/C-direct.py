import gurobipy as gp
from gurobipy import GRB

def solve(params):
    salary_F = params["salary_F"]
    salary_G = params["salary_G"]
    salary_H = params["salary_H"]
    salary_I = params["salary_I"]
    salary_J = params["salary_J"]
    budget = params["budget"]
    max_hires = params["max_hires"]
    skill_F = params["skill_F"]
    skill_G = params["skill_G"]
    skill_H = params["skill_H"]
    skill_I = params["skill_I"]
    skill_J = params["skill_J"]
    min_skill = params["min_skill"]
    exp_F = params["exp_F"]
    exp_G = params["exp_G"]
    exp_H = params["exp_H"]
    exp_I = params["exp_I"]
    exp_J = params["exp_J"]
    min_exp = params["min_exp"]

    model = gp.Model("hiring")
    model.setParam("OutputFlag", 0)

    # Binary decision variables: hire each candidate or not
    x_F = model.addVar(vtype=GRB.BINARY, name="x_F")
    x_G = model.addVar(vtype=GRB.BINARY, name="x_G")
    x_H = model.addVar(vtype=GRB.BINARY, name="x_H")
    x_I = model.addVar(vtype=GRB.BINARY, name="x_I")
    x_J = model.addVar(vtype=GRB.BINARY, name="x_J")

    # Objective: minimize total salary
    model.setObjective(
        salary_F * x_F + salary_G * x_G + salary_H * x_H + salary_I * x_I + salary_J * x_J,
        GRB.MINIMIZE
    )

    # Budget constraint
    model.addConstr(
        salary_F * x_F + salary_G * x_G + salary_H * x_H + salary_I * x_I + salary_J * x_J <= budget,
        name="budget"
    )

    # Maximum hires constraint
    model.addConstr(
        x_F + x_G + x_H + x_I + x_J <= max_hires,
        name="max_hires"
    )

    # Minimum total skill level constraint
    model.addConstr(
        skill_F * x_F + skill_G * x_G + skill_H * x_H + skill_I * x_I + skill_J * x_J >= min_skill,
        name="min_skill"
    )

    # Minimum total experience constraint
    model.addConstr(
        exp_F * x_F + exp_G * x_G + exp_H * x_H + exp_I * x_I + exp_J * x_J >= min_exp,
        name="min_exp"
    )

    # At most one of G or J (similar technical backgrounds)
    model.addConstr(
        x_G + x_J <= 1,
        name="G_or_J"
    )

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"status_{model.Status}"}