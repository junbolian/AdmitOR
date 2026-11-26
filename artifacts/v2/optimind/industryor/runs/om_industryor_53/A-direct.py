import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    math_req = params["math_requirement"]
    or_req = params["or_requirement"]
    cs_req = params["cs_requirement"]
    num_courses = params["num_courses"]

    courses = list(range(7))
    # 0 Calculus, 1 Operations Research, 2 Data Structures, 3 Management Statistics,
    # 4 Computer Simulation, 5 Computer Programming, 6 Forecasting

    math_courses = [0, 1, 2, 3, 6]
    or_courses = [1, 3, 4, 6]
    cs_courses = [2, 4, 5]

    # prerequisites: (course, prereq)
    prereqs = [(4, 5), (2, 5), (3, 0), (6, 3)]

    model = pyo.ConcreteModel()
    model.x = pyo.Var(courses, domain=pyo.Binary)

    model.math_con = pyo.Constraint(
        expr=sum(model.x[c] for c in math_courses) >= math_req
    )
    model.or_con = pyo.Constraint(
        expr=sum(model.x[c] for c in or_courses) >= or_req
    )
    model.cs_con = pyo.Constraint(
        expr=sum(model.x[c] for c in cs_courses) >= cs_req
    )
    model.total_con = pyo.Constraint(
        expr=sum(model.x[c] for c in courses) <= num_courses
    )

    model.prereq_cons = pyo.ConstraintList()
    for (course, pre) in prereqs:
        model.prereq_cons.add(model.x[course] <= model.x[pre])

    model.obj = pyo.Objective(expr=sum(model.x[c] for c in courses), sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}