import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    candidates = ["F", "G", "H", "I", "J"]

    salary_list = params["salary"]
    budget = params["budget"]
    max_hires = params["max_hires"]
    skill_list = params["skill"]
    min_total_skill = params["min_total_skill"]
    experience_list = params["experience"]
    min_total_experience = params["min_total_experience"]

    salary = dict(zip(candidates, salary_list))
    skill = dict(zip(candidates, skill_list))
    experience = dict(zip(candidates, experience_list))

    model = pyo.ConcreteModel()
    model.C = pyo.Set(initialize=candidates, ordered=True)

    model.x = pyo.Var(model.C, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(salary[c] * model.x[c] for c in model.C),
        sense=pyo.minimize,
    )

    model.budget_con = pyo.Constraint(
        expr=sum(salary[c] * model.x[c] for c in model.C) <= budget
    )

    model.max_hires_con = pyo.Constraint(
        expr=sum(model.x[c] for c in model.C) <= max_hires
    )

    model.skill_con = pyo.Constraint(
        expr=sum(skill[c] * model.x[c] for c in model.C) >= min_total_skill
    )

    model.exp_con = pyo.Constraint(
        expr=sum(experience[c] * model.x[c] for c in model.C) >= min_total_experience
    )

    model.excl_con = pyo.Constraint(expr=model.x["G"] + model.x["J"] <= 1)

    solver = Highs()
    solver.solve(model)

    try:
        obj_val = float(pyo.value(model.obj))
    except Exception:
        return {"objective": None, "status": "infeasible or no solution found"}

    return {"objective": obj_val, "status": "optimal"}