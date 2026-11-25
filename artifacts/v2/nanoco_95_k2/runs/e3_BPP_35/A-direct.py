import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    skill_scores = params["skill_scores"]
    max_load = params["max_skill_load_per_shift"]

    n = len(skill_scores)
    shifts = list(range(n))

    model = pyo.ConcreteModel()

    model.STAFF = pyo.RangeSet(0, n - 1)
    model.SHIFTS = pyo.RangeSet(0, n - 1)

    model.x = pyo.Var(model.STAFF, model.SHIFTS, domain=pyo.Binary)
    model.y = pyo.Var(model.SHIFTS, domain=pyo.Binary)

    def assign_rule(m, i):
        return sum(m.x[i, j] for j in m.SHIFTS) == 1

    model.assign_con = pyo.Constraint(model.STAFF, rule=assign_rule)

    def load_rule(m, j):
        return sum(skill_scores[i] * m.x[i, j] for i in m.STAFF) <= max_load * m.y[j]

    model.load_con = pyo.Constraint(model.SHIFTS, rule=load_rule)

    def link_rule(m, i, j):
        return m.x[i, j] <= m.y[j]

    model.link_con = pyo.Constraint(model.STAFF, model.SHIFTS, rule=link_rule)

    model.obj = pyo.Objective(expr=sum(model.y[j] for j in model.SHIFTS), sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}