# IR: {"sets":{"courses":["calculus","operations_research","data_structures","management_statistics","computer_simulation","computer_programming","forecasting"],"categories":["math","or","computer"],"membership":{"math":["calculus","operations_research","data_structures","management_statistics","forecasting"],"or":["operations_research","management_statistics","computer_simulation","forecasting"],"computer":["data_structures","computer_simulation","computer_programming"]},"prerequisites":[["computer_simulation","computer_programming"],["data_structures","computer_programming"],["management_statistics","calculus"],["forecasting","management_statistics"]]},"params":{"required_math_courses":"params['required_math_courses']","required_or_courses":"params['required_or_courses']","required_computer_courses":"params['required_computer_courses']"},"variables":{"take[course]":"binary"},"constraints":["sum(take[course] for course in membership[category]) >= required[category] for each category","take[course] <= take[prerequisite] for each prerequisite pair"],"objective":"minimize sum(take[course] for course in courses)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    courses = (
        "calculus",
        "operations_research",
        "data_structures",
        "management_statistics",
        "computer_simulation",
        "computer_programming",
        "forecasting",
    )
    categories = ("math", "or", "computer")

    membership = {
        "math": (
            "calculus",
            "operations_research",
            "data_structures",
            "management_statistics",
            "forecasting",
        ),
        "or": (
            "operations_research",
            "management_statistics",
            "computer_simulation",
            "forecasting",
        ),
        "computer": (
            "data_structures",
            "computer_simulation",
            "computer_programming",
        ),
    }

    prerequisites = (
        ("computer_simulation", "computer_programming"),
        ("data_structures", "computer_programming"),
        ("management_statistics", "calculus"),
        ("forecasting", "management_statistics"),
    )

    required = {
        "math": params["required_math_courses"],
        "or": params["required_or_courses"],
        "computer": params["required_computer_courses"],
    }

    model = pyo.ConcreteModel()
    model.courses = pyo.Set(initialize=courses, ordered=True)
    model.categories = pyo.Set(initialize=categories, ordered=True)
    model.prerequisite_pairs = pyo.Set(
        dimen=2, initialize=prerequisites, ordered=True
    )
    model.required = pyo.Param(
        model.categories, initialize=required, within=pyo.Reals
    )

    model.take = pyo.Var(model.courses, domain=pyo.Binary)

    def category_rule(current_model, category):
        return (
            sum(
                current_model.take[course]
                for course in membership[category]
            )
            >= current_model.required[category]
        )

    model.category_requirements = pyo.Constraint(
        model.categories, rule=category_rule
    )

    def prerequisite_rule(current_model, course, prerequisite):
        return current_model.take[course] <= current_model.take[prerequisite]

    model.prerequisite_requirements = pyo.Constraint(
        model.prerequisite_pairs, rule=prerequisite_rule
    )

    model.total_courses = pyo.Objective(
        expr=sum(model.take[course] for course in model.courses),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_courses))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}