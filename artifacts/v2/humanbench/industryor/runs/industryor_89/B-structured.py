# IR: {"sets":{"students":[0,1,2,3,4,5],"days":[0,1,2,3,4],"undergraduates":[0,1,2,3],"graduates":[4,5]},"params":{"remuneration":"length-6 array","max_hours":"6-by-5 array","opening_hours":"scalar","min_weekly_undergrad":"scalar","min_weekly_grad":"scalar","max_shifts_week":"scalar","max_students_per_day":"scalar"},"variables":{"hours[s,d]":"nonnegative continuous","assigned[s,d]":"binary"},"constraints":["For every day d: sum_s hours[s,d] = opening_hours.","For every student s and day d: hours[s,d] <= max_hours[s,d] * assigned[s,d].","For every undergraduate s: sum_d hours[s,d] >= min_weekly_undergrad.","For every graduate s: sum_d hours[s,d] >= min_weekly_grad.","For every student s: sum_d assigned[s,d] <= max_shifts_week.","For every day d: sum_s assigned[s,d] <= max_students_per_day."],"objective":"Minimize sum_{s,d} remuneration[s] * hours[s,d]."}

# Input arrays follow student order 1-6 and Monday-Friday.
# Each positive student-day allocation is scheduled as one consecutive shift.
# Because availability specifies daily hour limits rather than time windows,
# these shifts can be concatenated to cover the opening interval exactly.
#
# The original numerical instance is infeasible: Monday, Wednesday, and
# Friday each require at least three students, while Tuesday and Thursday
# each require at least two. This requires at least thirteen shifts, but
# six students working at most two shifts each can supply only twelve.
# A correct implementation must report failure for those inputs.

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    remuneration = params["remuneration"]
    max_hours = params["max_hours"]
    opening_hours = params["opening_hours"]
    min_weekly_undergrad = params["min_weekly_undergrad"]
    min_weekly_grad = params["min_weekly_grad"]
    max_shifts_week = params["max_shifts_week"]
    max_students_per_day = params["max_students_per_day"]

    model = pyo.ConcreteModel()

    model.students = pyo.RangeSet(0, 5)
    model.days = pyo.RangeSet(0, 4)
    model.undergraduates = pyo.RangeSet(0, 3)
    model.graduates = pyo.RangeSet(4, 5)

    model.hourly_pay = pyo.Param(
        model.students,
        initialize=lambda _, student: remuneration[student],
        within=pyo.NonNegativeReals,
    )
    model.daily_capacity = pyo.Param(
        model.students,
        model.days,
        initialize=lambda _, student, day: max_hours[student][day],
        within=pyo.NonNegativeReals,
    )
    model.daily_opening = pyo.Param(
        initialize=opening_hours,
        within=pyo.NonNegativeReals,
    )
    model.undergrad_minimum = pyo.Param(
        initialize=min_weekly_undergrad,
        within=pyo.NonNegativeReals,
    )
    model.grad_minimum = pyo.Param(
        initialize=min_weekly_grad,
        within=pyo.NonNegativeReals,
    )
    model.weekly_shift_limit = pyo.Param(
        initialize=max_shifts_week,
        within=pyo.NonNegativeIntegers,
    )
    model.daily_student_limit = pyo.Param(
        initialize=max_students_per_day,
        within=pyo.NonNegativeIntegers,
    )

    model.hours = pyo.Var(
        model.students,
        model.days,
        domain=pyo.NonNegativeReals,
    )
    model.assigned = pyo.Var(
        model.students,
        model.days,
        domain=pyo.Binary,
    )

    def daily_coverage_rule(_, day):
        return (
            sum(model.hours[student, day] for student in model.students)
            == model.daily_opening
        )

    model.daily_coverage = pyo.Constraint(
        model.days,
        rule=daily_coverage_rule,
    )

    def shift_capacity_rule(_, student, day):
        return (
            model.hours[student, day]
            <= model.daily_capacity[student, day]
            * model.assigned[student, day]
        )

    model.shift_capacity = pyo.Constraint(
        model.students,
        model.days,
        rule=shift_capacity_rule,
    )

    def undergraduate_minimum_rule(_, student):
        return (
            sum(model.hours[student, day] for day in model.days)
            >= model.undergrad_minimum
        )

    model.undergraduate_weekly_hours = pyo.Constraint(
        model.undergraduates,
        rule=undergraduate_minimum_rule,
    )

    def graduate_minimum_rule(_, student):
        return (
            sum(model.hours[student, day] for day in model.days)
            >= model.grad_minimum
        )

    model.graduate_weekly_hours = pyo.Constraint(
        model.graduates,
        rule=graduate_minimum_rule,
    )

    def weekly_shifts_rule(_, student):
        return (
            sum(model.assigned[student, day] for day in model.days)
            <= model.weekly_shift_limit
        )

    model.weekly_shifts = pyo.Constraint(
        model.students,
        rule=weekly_shifts_rule,
    )

    def daily_students_rule(_, day):
        return (
            sum(model.assigned[student, day] for student in model.students)
            <= model.daily_student_limit
        )

    model.daily_students = pyo.Constraint(
        model.days,
        rule=daily_students_rule,
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.hourly_pay[student] * model.hours[student, day]
            for student in model.students
            for day in model.days
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as error:
        # APPsi raises this when its default solution loading finds no
        # feasible solution. Unexpected runtime errors still propagate.
        if "A feasible solution was not found" not in str(error):
            raise

    try:
        obj_val = float(pyo.value(model.total_cost))
    except ValueError:
        return {"objective": None, "status": "no_solution"}

    return {"objective": obj_val, "status": "optimal"}