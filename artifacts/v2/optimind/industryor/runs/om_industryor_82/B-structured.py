# IR: {"sets":{"candidates":["A","B","C","D","E"],"advanced_degree":["B","C"]},"params":["salary_A","salary_B","salary_C","salary_D","salary_E","max_hires","budget","min_hires","experience_A","experience_B","experience_C","experience_D","experience_E","min_experience","max_from_A_E","min_advanced_degree"],"variables":{"hire[candidates]":"binary"},"constraints":["sum(hire[c] for c in candidates) <= max_hires","sum(hire[c] for c in candidates) >= min_hires","sum(salary[c]*hire[c] for c in candidates) <= budget","sum(experience[c]*hire[c] for c in candidates) >= min_experience","hire[A] + hire[E] <= max_from_A_E","sum(hire[c] for c in advanced_degree) >= min_advanced_degree"],"objective":"minimize sum(salary[c]*hire[c] for c in candidates)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.candidates = pyo.Set(
        initialize=["A", "B", "C", "D", "E"], ordered=True
    )
    model.advanced_degree = pyo.Set(
        initialize=["B", "C"], within=model.candidates
    )

    model.salary = pyo.Param(
        model.candidates,
        initialize={
            "A": params["salary_A"],
            "B": params["salary_B"],
            "C": params["salary_C"],
            "D": params["salary_D"],
            "E": params["salary_E"],
        },
        within=pyo.Reals,
    )
    model.experience = pyo.Param(
        model.candidates,
        initialize={
            "A": params["experience_A"],
            "B": params["experience_B"],
            "C": params["experience_C"],
            "D": params["experience_D"],
            "E": params["experience_E"],
        },
        within=pyo.Reals,
    )
    model.max_hires = pyo.Param(initialize=params["max_hires"])
    model.budget = pyo.Param(initialize=params["budget"])
    model.min_hires = pyo.Param(initialize=params["min_hires"])
    model.min_experience = pyo.Param(initialize=params["min_experience"])
    model.max_from_A_E = pyo.Param(initialize=params["max_from_A_E"])
    model.min_advanced_degree = pyo.Param(
        initialize=params["min_advanced_degree"]
    )

    model.hire = pyo.Var(model.candidates, domain=pyo.Binary)

    model.maximum_hires_constraint = pyo.Constraint(
        expr=sum(model.hire[c] for c in model.candidates) <= model.max_hires
    )
    model.minimum_hires_constraint = pyo.Constraint(
        expr=sum(model.hire[c] for c in model.candidates) >= model.min_hires
    )
    model.budget_constraint = pyo.Constraint(
        expr=sum(
            model.salary[c] * model.hire[c] for c in model.candidates
        ) <= model.budget
    )
    model.experience_constraint = pyo.Constraint(
        expr=sum(
            model.experience[c] * model.hire[c] for c in model.candidates
        ) >= model.min_experience
    )
    model.equivalent_skills_constraint = pyo.Constraint(
        expr=model.hire["A"] + model.hire["E"] <= model.max_from_A_E
    )
    model.advanced_degree_constraint = pyo.Constraint(
        expr=sum(
            model.hire[c] for c in model.advanced_degree
        ) >= model.min_advanced_degree
    )

    model.total_payment = pyo.Objective(
        expr=sum(
            model.salary[c] * model.hire[c] for c in model.candidates
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_payment))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}