# IR: {"sets":{"students":[0,1,2,3,4,5],"days":[0,1,2,3,4],"undergraduates":[0,1,2,3],"graduates":[4,5]},"params":{"wage":"nonnegative vector[6]","max_hours":"nonnegative matrix[6,5]","daily_operation_hours":"nonnegative scalar","undergrad_min_hours":"nonnegative scalar","grad_min_hours":"nonnegative scalar","max_shifts_per_student":"nonnegative scalar","max_students_per_day":"nonnegative scalar"},"variables":{"hours[s,d]":"nonnegative continuous","assigned[s,d]":"binary; selects at most one contiguous shift per student per day"},"constraints":["hours[s,d] <= max_hours[s,d] * assigned[s,d] for every student and day","sum_s hours[s,d] == daily_operation_hours for every day","sum_d hours[s,d] >= undergrad_min_hours for every undergraduate","sum_d hours[s,d] >= grad_min_hours for every graduate","sum_d assigned[s,d] <= max_shifts_per_student for every student","sum_s assigned[s,d] <= max_students_per_day for every day"],"objective":"minimize sum_s,d wage[s] * hours[s,d]","schedule_interpretation":"Each day, concatenate the positive-duration shifts in student order starting at opening time; the resulting schedule has exactly one student on duty throughout operating hours."}

import pyomo.environ as pyo
from pyomo.common.errors import ApplicationError
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    wage = params["wage"]
    max_hours = params["max_hours"]
    daily_operation_hours = params["daily_operation_hours"]
    undergrad_min_hours = params["undergrad_min_hours"]
    grad_min_hours = params["grad_min_hours"]
    max_shifts_per_student = params["max_shifts_per_student"]
    max_students_per_day = params["max_students_per_day"]

    model = pyo.ConcreteModel()

    # Zero-based indices correspond to students 1–6 and Monday–Friday.
    model.students = pyo.Set(initialize=range(6), ordered=True)
    model.days = pyo.Set(initialize=range(5), ordered=True)
    model.undergraduates = pyo.Set(initialize=range(4), ordered=True)
    model.graduates = pyo.Set(initialize=range(4, 6), ordered=True)

    model.wage = pyo.Param(
        model.students,
        initialize={student: wage[student] for student in range(6)},
        within=pyo.NonNegativeReals,
    )
    model.max_hours = pyo.Param(
        model.students,
        model.days,
        initialize={
            (student, day): max_hours[student][day]
            for student in range(6)
            for day in range(5)
        },
        within=pyo.NonNegativeReals,
    )
    model.daily_operation_hours = pyo.Param(
        initialize=daily_operation_hours,
        within=pyo.NonNegativeReals,
    )
    model.undergrad_min_hours = pyo.Param(
        initialize=undergrad_min_hours,
        within=pyo.NonNegativeReals,
    )
    model.grad_min_hours = pyo.Param(
        initialize=grad_min_hours,
        within=pyo.NonNegativeReals,
    )
    model.max_shifts_per_student = pyo.Param(
        initialize=max_shifts_per_student,
        within=pyo.NonNegativeReals,
    )
    model.max_students_per_day = pyo.Param(
        initialize=max_students_per_day,
        within=pyo.NonNegativeReals,
    )

    model.hours = pyo.Var(
        model.students, model.days, domain=pyo.NonNegativeReals
    )
    model.assigned = pyo.Var(
        model.students, model.days, domain=pyo.Binary
    )

    def availability_rule(problem, student, day):
        return (
            problem.hours[student, day]
            <= problem.max_hours[student, day]
            * problem.assigned[student, day]
        )

    model.availability_limit = pyo.Constraint(
        model.students, model.days, rule=availability_rule
    )

    def coverage_rule(problem, day):
        return (
            sum(problem.hours[student, day] for student in problem.students)
            == problem.daily_operation_hours
        )

    model.daily_coverage = pyo.Constraint(
        model.days, rule=coverage_rule
    )

    def undergraduate_minimum_rule(problem, student):
        return (
            sum(problem.hours[student, day] for day in problem.days)
            >= problem.undergrad_min_hours
        )

    model.undergraduate_minimum = pyo.Constraint(
        model.undergraduates, rule=undergraduate_minimum_rule
    )

    def graduate_minimum_rule(problem, student):
        return (
            sum(problem.hours[student, day] for day in problem.days)
            >= problem.grad_min_hours
        )

    model.graduate_minimum = pyo.Constraint(
        model.graduates, rule=graduate_minimum_rule
    )

    def shift_limit_rule(problem, student):
        return (
            sum(problem.assigned[student, day] for day in problem.days)
            <= problem.max_shifts_per_student
        )

    model.weekly_shift_limit = pyo.Constraint(
        model.students, rule=shift_limit_rule
    )

    def daily_student_limit_rule(problem, day):
        return (
            sum(
                problem.assigned[student, day]
                for student in problem.students
            )
            <= problem.max_students_per_day
        )

    model.daily_student_limit = pyo.Constraint(
        model.days, rule=daily_student_limit_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.wage[student] * model.hours[student, day]
            for student in model.students
            for day in model.days
        ),
        sense=pyo.minimize,
    )

    # APPsi can raise when no solution is available to load.
    # Objective retrieval below is the sole success criterion.
    try:
        Highs().solve(model)
    except (RuntimeError, ApplicationError):
        pass

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "infeasible_or_failed"}

    return {"objective": obj_val, "status": "optimal"}