# IR: {"sets":{"C":["F","G","H","I","J"]},"params":{"salary":{"F":"salary_F","G":"salary_G","H":"salary_H","I":"salary_I","J":"salary_J"},"skill":{"F":"skill_F","G":"skill_G","H":"skill_H","I":"skill_I","J":"skill_J"},"experience":{"F":"exp_F","G":"exp_G","H":"exp_H","I":"exp_I","J":"exp_J"},"budget":"budget","max_hires":"max_hires","min_skill":"min_skill","min_exp":"min_exp"},"variables":{"hire[c in C]":"binary"},"constraints":["sum(salary[c]*hire[c] for c in C) <= budget","sum(hire[c] for c in C) <= max_hires","sum(skill[c]*hire[c] for c in C) >= min_skill","sum(experience[c]*hire[c] for c in C) >= min_exp","hire[G] + hire[J] <= 1"],"objective":{"sense":"minimize","expression":"sum(salary[c]*hire[c] for c in C)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.candidates = pyo.Set(
        initialize=["F", "G", "H", "I", "J"], ordered=True
    )

    model.salary = pyo.Param(
        model.candidates,
        initialize={
            "F": params["salary_F"],
            "G": params["salary_G"],
            "H": params["salary_H"],
            "I": params["salary_I"],
            "J": params["salary_J"],
        },
    )
    model.skill = pyo.Param(
        model.candidates,
        initialize={
            "F": params["skill_F"],
            "G": params["skill_G"],
            "H": params["skill_H"],
            "I": params["skill_I"],
            "J": params["skill_J"],
        },
    )
    model.experience = pyo.Param(
        model.candidates,
        initialize={
            "F": params["exp_F"],
            "G": params["exp_G"],
            "H": params["exp_H"],
            "I": params["exp_I"],
            "J": params["exp_J"],
        },
    )
    model.budget = pyo.Param(initialize=params["budget"])
    model.max_hires = pyo.Param(initialize=params["max_hires"])
    model.min_skill = pyo.Param(initialize=params["min_skill"])
    model.min_exp = pyo.Param(initialize=params["min_exp"])

    model.hire = pyo.Var(model.candidates, domain=pyo.Binary)

    model.total_salary = pyo.Objective(
        expr=sum(
            model.salary[candidate] * model.hire[candidate]
            for candidate in model.candidates
        ),
        sense=pyo.minimize,
    )

    model.budget_limit = pyo.Constraint(
        expr=sum(
            model.salary[candidate] * model.hire[candidate]
            for candidate in model.candidates
        ) <= model.budget
    )
    model.hiring_limit = pyo.Constraint(
        expr=sum(
            model.hire[candidate] for candidate in model.candidates
        ) <= model.max_hires
    )
    model.skill_requirement = pyo.Constraint(
        expr=sum(
            model.skill[candidate] * model.hire[candidate]
            for candidate in model.candidates
        ) >= model.min_skill
    )
    model.experience_requirement = pyo.Constraint(
        expr=sum(
            model.experience[candidate] * model.hire[candidate]
            for candidate in model.candidates
        ) >= model.min_exp
    )
    model.background_exclusion = pyo.Constraint(
        expr=model.hire["G"] + model.hire["J"] <= 1
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_salary))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}