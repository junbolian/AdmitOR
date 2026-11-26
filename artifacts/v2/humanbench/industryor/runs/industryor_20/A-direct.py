import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    required_math = params["required_math_courses"]
    required_or = params["required_or_courses"]
    required_comp = params["required_computer_courses"]

    # Courses index: 0..6
    # 0 calculus, 1 operations research, 2 data structures,
    # 3 management statistics, 4 computer simulation, 5 computer programming,
    # 6 forecasting
    courses = range(7)

    # Category membership
    math_courses = [0, 1, 2, 3, 6]       # calculus, OR, data structures, mgmt stats, forecasting
    or_courses = [1, 3, 4, 6]            # OR, mgmt stats, comp sim, forecasting
    comp_courses = [2, 4, 5]             # data structures, comp sim, comp programming

    # Prerequisites: (course, prereq)
    prereqs = [
        (4, 5),   # comp sim after comp programming
        (2, 5),   # data structures after comp programming
        (3, 0),   # mgmt stats after calculus
        (6, 3),   # forecasting after mgmt stats
    ]

    model = pyo.ConcreteModel()

    model.x = pyo.Var(courses, domain=pyo.Binary)

    # Requirements
    model.math_req = pyo.Constraint(
        expr=sum(model.x[c] for c in math_courses) >= required_math
    )
    model.or_req = pyo.Constraint(
        expr=sum(model.x[c] for c in or_courses) >= required_or
    )
    model.comp_req = pyo.Constraint(
        expr=sum(model.x[c] for c in comp_courses) >= required_comp
    )

    # Prerequisites
    model.prereq_con = pyo.Constraint(
        prereqs,
        rule=lambda model, c, p: model.x[c] <= model.x[p]
    )

    model.obj = pyo.Objective(expr=sum(model.x[c] for c in courses), sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}