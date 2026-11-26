# IR: {"sets":{"candidates":["A","B","C","D","E"],"advanced":["B","C"],"similar":["A","E"]},"params":{"salary":"salary_A,...,salary_E","experience":"experience_A,...,experience_E","max_hires":"max_hires","min_hires":"min_hires","budget":"budget","min_experience":"min_experience","AE_max":"AE_max","min_advanced_degree":"min_advanced_degree"},"variables":{"hire[candidates]":"Binary"},"constraints":{"maximum_hires":"sum(hire[c] for c in candidates) <= max_hires","minimum_hires":"sum(hire[c] for c in candidates) >= min_hires","payment_budget":"sum(salary[c]*hire[c] for c in candidates) <= budget","required_experience":"sum(experience[c]*hire[c] for c in candidates) >= min_experience","similar_candidates":"sum(hire[c] for c in similar) <= AE_max","advanced_degree_requirement":"sum(hire[c] for c in advanced) >= min_advanced_degree"},"objective":{"sense":"minimize","expression":"sum(salary[c]*hire[c] for c in candidates)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.candidates = pyo.Set(
        initialize=("A", "B", "C", "D", "E"), ordered=True
    )
    model.advanced = pyo.Set(
        initialize=("B", "C"), within=model.candidates
    )
    model.similar = pyo.Set(
        initialize=("A", "E"), within=model.candidates
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
    )
    model.max_hires = pyo.Param(initialize=params["max_hires"])
    model.min_hires = pyo.Param(initialize=params["min_hires"])
    model.budget = pyo.Param(initialize=params["budget"])
    model.min_experience = pyo.Param(initialize=params["min_experience"])
    model.AE_max = pyo.Param(initialize=params["AE_max"])
    model.min_advanced_degree = pyo.Param(
        initialize=params["min_advanced_degree"]
    )

    model.hire = pyo.Var(model.candidates, domain=pyo.Binary)

    model.maximum_hires = pyo.Constraint(
        expr=sum(model.hire[c] for c in model.candidates)
        <= model.max_hires
    )
    model.minimum_hires = pyo.Constraint(
        expr=sum(model.hire[c] for c in model.candidates)
        >= model.min_hires
    )
    model.payment_budget = pyo.Constraint(
        expr=sum(
            model.salary[c] * model.hire[c] for c in model.candidates
        )
        <= model.budget
    )
    model.required_experience = pyo.Constraint(
        expr=sum(
            model.experience[c] * model.hire[c]
            for c in model.candidates
        )
        >= model.min_experience
    )
    model.similar_candidates = pyo.Constraint(
        expr=sum(model.hire[c] for c in model.similar)
        <= model.AE_max
    )
    model.advanced_degree_requirement = pyo.Constraint(
        expr=sum(model.hire[c] for c in model.advanced)
        >= model.min_advanced_degree
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