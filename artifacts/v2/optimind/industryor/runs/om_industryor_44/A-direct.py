import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    # Structural constants
    students = [1, 2, 3, 4, 5, 6]
    undergrads = [1, 2, 3, 4]
    grads = [5, 6]
    days = [1, 2, 3, 4, 5]
    hours = list(range(8, 22))  # 8:00 to 22:00, 14 one-hour slots

    wage = params["wage"]
    max_hours = params["max_hours"]
    undergrad_min_hours = params["undergrad_min_hours"]
    grad_min_hours = params["grad_min_hours"]
    max_shifts_per_student = params["max_shifts_per_student"]
    max_students_per_day = params["max_students_per_day"]

    model = pyo.ConcreteModel()

    model.S = pyo.Set(initialize=students)
    model.U = pyo.Set(initialize=undergrads)
    model.G = pyo.Set(initialize=grads)
    model.D = pyo.Set(initialize=days)
    model.H = pyo.Set(initialize=hours)

    model.x = pyo.Var(model.S, model.D, model.H, domain=pyo.Binary)
    model.y = pyo.Var(model.S, model.D, domain=pyo.Binary)
    model.w = pyo.Var(model.S, model.D, model.H, domain=pyo.Binary)

    def obj_rule(m):
        return sum(m.x[s, d, h] * wage[s - 1] for s in m.S for d in m.D for h in m.H)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Exactly one student per hour
    def cover_rule(m, d, h):
        return sum(m.x[s, d, h] for s in m.S) == 1
    model.cover = pyo.Constraint(model.D, model.H, rule=cover_rule)

    # Max hours per student per day
    def day_max_rule(m, s, d):
        return sum(m.x[s, d, h] for h in m.H) <= max_hours[s - 1][d - 1]
    model.day_max = pyo.Constraint(model.S, model.D, rule=day_max_rule)

    # Weekly minimums
    def undergrad_min_rule(m, s):
        return sum(m.x[s, d, h] for d in m.D for h in m.H) >= undergrad_min_hours
    model.ug_min = pyo.Constraint(model.U, rule=undergrad_min_rule)

    def grad_min_rule(m, s):
        return sum(m.x[s, d, h] for d in m.D for h in m.H) >= grad_min_hours
    model.g_min = pyo.Constraint(model.G, rule=grad_min_rule)

    # Link y to x: y[s,d]=1 if student works at least one hour on day d
    def y_lb_rule(m, s, d, h):
        return m.x[s, d, h] <= m.y[s, d]
    model.y_lb = pyo.Constraint(model.S, model.D, model.H, rule=y_lb_rule)

    def y_ub_rule(m, s, d):
        return m.y[s, d] <= sum(m.x[s, d, h] for h in m.H)
    model.y_ub = pyo.Constraint(model.S, model.D, rule=y_ub_rule)

    # Max distinct students per day
    def day_students_rule(m, d):
        return sum(m.y[s, d] for s in m.S) <= max_students_per_day
    model.day_students = pyo.Constraint(model.D, rule=day_students_rule)

    # w = start-of-shift indicator: w[s,d,h]=1 if shift starts at h
    # w[s,d,h] <= x[s,d,h]
    def w_le_x_rule(m, s, d, h):
        return m.w[s, d, h] <= m.x[s, d, h]
    model.w_le_x = pyo.Constraint(model.S, model.D, model.H, rule=w_le_x_rule)

    # Start of shift: w[s,d,h]=1 requires x[s,d,h]=1 and (h==first hour or x[s,d,h-1]=0)
    # Enforce: x[s,d,h] - x[s,d,h-1] <= w[s,d,h] for h >= 9
    def w_continuity_rule(m, s, d, h):
        if h == hours[0]:
            return pyo.Constraint.Skip
        return m.x[s, d, h] - m.x[s, d, h - 1] <= m.w[s, d, h]
    model.w_continuity = pyo.Constraint(model.S, model.D, model.H, rule=w_continuity_rule)

    # First hour shift start
    def w_first_rule(m, s, d):
        return m.w[s, d, hours[0]] >= m.x[s, d, hours[0]]
    model.w_first = pyo.Constraint(model.S, model.D, rule=w_first_rule)

    # Max shifts per student per week
    def max_shifts_rule(m, s):
        return sum(m.w[s, d, h] for d in m.D for h in m.H) <= max_shifts_per_student
    model.max_shifts = pyo.Constraint(model.S, rule=max_shifts_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}