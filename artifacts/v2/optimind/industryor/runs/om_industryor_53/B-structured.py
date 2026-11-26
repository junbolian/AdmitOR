# IR: {"sets":{"C":["Calculus","Operations Research","Data Structures","Management Statistics","Computer Simulation","Computer Programming","Forecasting"],"MATH":["Calculus","Operations Research","Data Structures","Management Statistics","Forecasting"],"OR":["Operations Research","Management Statistics","Computer Simulation","Forecasting"],"CS":["Data Structures","Computer Simulation","Computer Programming"],"PREREQ":[["Computer Simulation","Computer Programming"],["Data Structures","Computer Programming"],["Management Statistics","Calculus"],["Forecasting","Management Statistics"]]},"params":{"math_requirement":"nonnegative integer","or_requirement":"nonnegative integer","cs_requirement":"nonnegative integer","num_courses":"integer equal to |C|; otherwise return invalid_num_courses"},"variables":{"x[c]":"binary for c in C"},"constraints":["sum(x[c] for c in MATH) >= math_requirement","sum(x[c] for c in OR) >= or_requirement","sum(x[c] for c in CS) >= cs_requirement","x[course] <= x[prerequisite] for (course,prerequisite) in PREREQ"],"objective":"minimize sum(x[c] for c in C)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    math_requirement = params["math_requirement"]
    or_requirement = params["or_requirement"]
    cs_requirement = params["cs_requirement"]
    num_courses = params["num_courses"]

    courses = (
        "Calculus",
        "Operations Research",
        "Data Structures",
        "Management Statistics",
        "Computer Simulation",
        "Computer Programming",
        "Forecasting",
    )

    # The problem provides category and prerequisite data for this catalog only.
    if num_courses != len(courses):
        return {"objective": None, "status": "invalid_num_courses"}

    model = pyo.ConcreteModel()

    model.course_set = pyo.Set(initialize=courses, ordered=True)

    model.math_courses = pyo.Set(
        within=model.course_set,
        initialize=(
            "Calculus",
            "Operations Research",
            "Data Structures",
            "Management Statistics",
            "Forecasting",
        ),
    )
    model.or_courses = pyo.Set(
        within=model.course_set,
        initialize=(
            "Operations Research",
            "Management Statistics",
            "Computer Simulation",
            "Forecasting",
        ),
    )
    model.cs_courses = pyo.Set(
        within=model.course_set,
        initialize=(
            "Data Structures",
            "Computer Simulation",
            "Computer Programming",
        ),
    )
    model.prerequisite_pairs = pyo.Set(
        dimen=2,
        within=model.course_set * model.course_set,
        initialize=(
            ("Computer Simulation", "Computer Programming"),
            ("Data Structures", "Computer Programming"),
            ("Management Statistics", "Calculus"),
            ("Forecasting", "Management Statistics"),
        ),
    )

    model.math_requirement = pyo.Param(
        initialize=math_requirement, within=pyo.NonNegativeIntegers
    )
    model.or_requirement = pyo.Param(
        initialize=or_requirement, within=pyo.NonNegativeIntegers
    )
    model.cs_requirement = pyo.Param(
        initialize=cs_requirement, within=pyo.NonNegativeIntegers
    )
    model.num_courses = pyo.Param(
        initialize=num_courses, within=pyo.NonNegativeIntegers
    )

    model.x = pyo.Var(model.course_set, domain=pyo.Binary)

    model.math_coverage = pyo.Constraint(
        expr=sum(model.x[course] for course in model.math_courses)
        >= model.math_requirement
    )
    model.or_coverage = pyo.Constraint(
        expr=sum(model.x[course] for course in model.or_courses)
        >= model.or_requirement
    )
    model.cs_coverage = pyo.Constraint(
        expr=sum(model.x[course] for course in model.cs_courses)
        >= model.cs_requirement
    )

    def prerequisite_rule(instance, course, prerequisite):
        return instance.x[course] <= instance.x[prerequisite]

    model.prerequisite_constraints = pyo.Constraint(
        model.prerequisite_pairs, rule=prerequisite_rule
    )

    model.total_courses = pyo.Objective(
        expr=sum(model.x[course] for course in model.course_set),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "infeasible_or_failed"}

    try:
        obj_val = float(pyo.value(model.total_courses))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}