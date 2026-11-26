import gurobipy as gp
from gurobipy import GRB

def solve(params):
    salary = params["salary"]           # list indexed 0..4 for F,G,H,I,J
    budget = params["budget"]
    max_hires = params["max_hires"]
    skill = params["skill"]
    min_total_skill = params["min_total_skill"]
    experience = params["experience"]
    min_total_experience = params["min_total_experience"]

    candidates = ["F", "G", "H", "I", "J"]
    idx = {c: i for i, c in enumerate(candidates)}

    def sal(c):
        v = salary[idx[c]] if isinstance(salary, (list, tuple)) else salary[c]
        return v

    def skl(c):
        v = skill[idx[c]] if isinstance(skill, (list, tuple)) else skill[c]
        return v

    def exp(c):
        v = experience[idx[c]] if isinstance(experience, (list, tuple)) else experience[c]
        return v

    model = gp.Model("hiring")
    model.setParam("OutputFlag", 0)

    x = model.addVars(candidates, vtype=GRB.BINARY, name="x")

    model.setObjective(
        gp.quicksum(sal(c) * x[c] for c in candidates),
        GRB.MINIMIZE
    )

    model.addConstr(
        gp.quicksum(sal(c) * x[c] for c in candidates) <= budget,
        name="budget"
    )

    model.addConstr(
        gp.quicksum(x[c] for c in candidates) <= max_hires,
        name="max_hires"
    )

    model.addConstr(
        gp.quicksum(skl(c) * x[c] for c in candidates) >= min_total_skill,
        name="min_skill"
    )

    model.addConstr(
        gp.quicksum(exp(c) * x[c] for c in candidates) >= min_total_experience,
        name="min_experience"
    )

    model.addConstr(x["G"] + x["J"] <= 1, name="G_or_J")

    model.optimize()

    if model.Status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif model.Status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif model.Status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{model.Status}"}