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

    students = list(range(1, 7))
    days = list(range(1, 6))
    undergrads = [1, 2, 3, 4]
    grads = [5, 6]

    model = pyo.ConcreteModel()

    model.S = pyo.Set(initialize=students, ordered=True)
    model.D = pyo.Set(initialize=days, ordered=True)

    def x_bounds(mdl, s, d):
        return (0, max_hours[s - 1][d - 1])

    model.x = pyo.Var(model.S, model.D, domain=pyo.NonNegativeReals,
                      bounds=x_bounds)
    model.y = pyo.Var(model.S, model.D, domain=pyo.Binary)

    # Link assignment to hours
    def shift_link_ub(mdl, s, d):
        return mdl.x[s, d] <= max_hours[s - 1][d - 1] * mdl.y[s, d]
    model.shift_link_ub = pyo.Constraint(model.S, model.D, rule=shift_link_ub)

    # Daily coverage: exactly opening_hours total across students
    def daily_coverage(mdl, d):
        return sum(mdl.x[s, d] for s in mdl.S) == opening_hours
    model.daily_coverage = pyo.Constraint(model.D, rule=daily_coverage)

    # Weekly minimum for undergraduates
    def min_week_undergrad(mdl, s):
        return sum(mdl.x[s, d] for d in mdl.D) >= min_weekly_undergrad
    model.min_week_undergrad = pyo.Constraint(pyo.Set(initialize=undergrads),
                                              rule=min_week_undergrad)

    # Weekly minimum for graduates
    def min_week_grad(mdl, s):
        return sum(mdl.x[s, d] for d in mdl.D) >= min_weekly_grad
    model.min_week_grad = pyo.Constraint(pyo.Set(initialize=grads),
                                         rule=min_week_grad)

    # Maximum shifts per week per student
    def max_shifts(mdl, s):
        return sum(mdl.y[s, d] for d in mdl.D) <= max_shifts_week
    model.max_shifts = pyo.Constraint(model.S, rule=max_shifts)

    # Maximum students per day
    def max_students_day(mdl, d):
        return sum(mdl.y[s, d] for s in mdl.S) <= max_students_per_day
    model.max_students_day = pyo.Constraint(model.D, rule=max_students_day)

    # Objective: minimize total remuneration cost
    def obj_rule(mdl):
        return sum(remuneration[s - 1] * mdl.x[s, d]
                   for s in mdl.S for d in mdl.D)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}