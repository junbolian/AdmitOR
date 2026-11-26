# IR: {"sets":{"C":["F","G","H","I","J"]},"params":{"salary":"nonnegative values indexed by C or sequence in C order","budget":"nonnegative real","max_hires":"nonnegative integer","skill":"nonnegative values indexed by C or sequence in C order","min_total_skill":"nonnegative real","experience":"nonnegative values indexed by C or sequence in C order","min_total_experience":"nonnegative real"},"variables":{"hire[c]":"binary for c in C"},"constraints":["sum(salary[c]*hire[c] for c in C) <= budget","sum(hire[c] for c in C) <= max_hires","sum(skill[c]*hire[c] for c in C) >= min_total_skill","sum(experience[c]*hire[c] for c in C) >= min_total_experience","hire[G] + hire[J] <= 1"],"objective":"minimize sum(salary[c]*hire[c] for c in C)"}

from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    candidates = ("F", "G", "H", "I", "J")

    def candidate_values(values):
        if isinstance(values, Mapping):
            return {candidate: values[candidate] for candidate in candidates}
        if len(values) != len(candidates):
            raise ValueError("Candidate sequences must contain five values.")
        return {
            candidate: values[position]
            for position, candidate in enumerate(candidates)
        }

    model = pyo.ConcreteModel()
    model.C = pyo.Set(initialize=candidates, ordered=True)

    model.salary = pyo.Param(
        model.C,
        initialize=candidate_values(params["salary"]),
        within=pyo.NonNegativeReals,
    )
    model.budget = pyo.Param(
        initialize=params["budget"],
        within=pyo.NonNegativeReals,
    )
    model.max_hires = pyo.Param(
        initialize=params["max_hires"],
        within=pyo.NonNegativeIntegers,
    )
    model.skill = pyo.Param(
        model.C,
        initialize=candidate_values(params["skill"]),
        within=pyo.NonNegativeReals,
    )
    model.min_total_skill = pyo.Param(
        initialize=params["min_total_skill"],
        within=pyo.NonNegativeReals,
    )
    model.experience = pyo.Param(
        model.C,
        initialize=candidate_values(params["experience"]),
        within=pyo.NonNegativeReals,
    )
    model.min_total_experience = pyo.Param(
        initialize=params["min_total_experience"],
        within=pyo.NonNegativeReals,
    )

    model.hire = pyo.Var(model.C, domain=pyo.Binary)

    model.budget_limit = pyo.Constraint(
        expr=sum(model.salary[c] * model.hire[c] for c in model.C)
        <= model.budget
    )
    model.hiring_limit = pyo.Constraint(
        expr=sum(model.hire[c] for c in model.C) <= model.max_hires
    )
    model.skill_requirement = pyo.Constraint(
        expr=sum(model.skill[c] * model.hire[c] for c in model.C)
        >= model.min_total_skill
    )
    model.experience_requirement = pyo.Constraint(
        expr=sum(model.experience[c] * model.hire[c] for c in model.C)
        >= model.min_total_experience
    )
    model.background_limit = pyo.Constraint(
        expr=model.hire["G"] + model.hire["J"] <= 1
    )

    model.total_salary = pyo.Objective(
        expr=sum(model.salary[c] * model.hire[c] for c in model.C),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_salary))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}