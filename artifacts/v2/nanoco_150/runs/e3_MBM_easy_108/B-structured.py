# IR: {"sets":{"patients":[0,1,2,3,4],"rooms":[0,1,2,3,4,5,6],"compatible_pairs":[[0,0],[0,2],[0,4],[0,5],[1,2],[1,6],[2,0],[2,2],[2,3],[3,0],[3,4],[4,1],[4,2],[4,3],[4,4]]},"params":{},"variables":{"assigned[p,r]":{"domain":"Binary","indices":"compatible_pairs"}},"constraints":["For each patient p: sum(assigned[p,r] for compatible rooms r) <= 1","For each room r: sum(assigned[p,r] for compatible patients p) <= 1"],"objective":{"sense":"maximize","expression":"sum(assigned[p,r] for (p,r) in compatible_pairs)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.patients = pyo.Set(initialize=range(5), ordered=True)
    model.rooms = pyo.Set(initialize=range(7), ordered=True)
    model.compatible_pairs = pyo.Set(
        dimen=2,
        within=model.patients * model.rooms,
        initialize=[
            (0, 0), (0, 2), (0, 4), (0, 5),
            (1, 2), (1, 6),
            (2, 0), (2, 2), (2, 3),
            (3, 0), (3, 4),
            (4, 1), (4, 2), (4, 3), (4, 4),
        ],
        ordered=True,
    )

    model.assigned = pyo.Var(model.compatible_pairs, domain=pyo.Binary)

    def patient_limit_rule(model, patient):
        return sum(
            model.assigned[patient, room]
            for room in model.rooms
            if (patient, room) in model.compatible_pairs
        ) <= 1

    model.patient_limit = pyo.Constraint(
        model.patients, rule=patient_limit_rule
    )

    def room_limit_rule(model, room):
        return sum(
            model.assigned[patient, room]
            for patient in model.patients
            if (patient, room) in model.compatible_pairs
        ) <= 1

    model.room_limit = pyo.Constraint(model.rooms, rule=room_limit_rule)

    model.total_sessions = pyo.Objective(
        expr=sum(
            model.assigned[patient, room]
            for patient, room in model.compatible_pairs
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_sessions))
    except ValueError:
        return {"objective": None, "status": "no_objective"}

    return {"objective": obj_val, "status": "optimal"}