import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    skill_scores = params["skill_scores"]
    shift_capacity = params["shift_capacity"]

    n_staff = len(skill_scores)
    n_shifts = n_staff

    model = pyo.ConcreteModel()
    model.STAFF = pyo.Set(initialize=range(n_staff))
    model.SHIFTS = pyo.Set(initialize=range(n_shifts))

    model.x = pyo.Var(model.STAFF, model.SHIFTS, domain=pyo.Binary)
    model.y = pyo.Var(model.SHIFTS, domain=pyo.Binary)

    model.assign = pyo.Constraint(
        model.STAFF,
        rule=lambda m, i: sum(m.x[i, j] for j in m.SHIFTS) == 1,
    )
    model.capacity = pyo.Constraint(
        model.SHIFTS,
        rule=lambda m, j: sum(
            skill_scores[i] * m.x[i, j] for i in m.STAFF
        ) <= shift_capacity * m.y[j],
    )
    model.link = pyo.Constraint(
        model.STAFF,
        model.SHIFTS,
        rule=lambda m, i, j: m.x[i, j] <= m.y[j],
    )

    model.obj = pyo.Objective(
        expr=sum(model.y[j] for j in model.SHIFTS), sense=pyo.minimize
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}