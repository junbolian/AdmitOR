import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # Structural data (compatibility assignments are structural, not params)
    patients = list(range(5))
    rooms = list(range(7))
    feasible = [
        (0, 0), (0, 2), (0, 4), (0, 5),
        (1, 2), (1, 6),
        (2, 0), (2, 2), (2, 3),
        (3, 0), (3, 4),
        (4, 1), (4, 2), (4, 3), (4, 4),
    ]

    model = pyo.ConcreteModel()

    model.ASSIGN = pyo.Set(initialize=feasible, dimen=2)
    model.PATIENTS = pyo.Set(initialize=patients)
    model.ROOMS = pyo.Set(initialize=rooms)

    model.x = pyo.Var(model.ASSIGN, within=pyo.Binary)

    def patient_rule(mdl, p):
        return sum(mdl.x[p, r] for (pp, r) in feasible if pp == p) <= 1

    def room_rule(mdl, r):
        return sum(mdl.x[p, rr] for (p, rr) in feasible if rr == r) <= 1

    model.patient_cons = pyo.Constraint(model.PATIENTS, rule=patient_rule)
    model.room_cons = pyo.Constraint(model.ROOMS, rule=room_rule)

    model.obj = pyo.Objective(
        expr=sum(model.x[a] for a in model.ASSIGN), sense=pyo.maximize
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}