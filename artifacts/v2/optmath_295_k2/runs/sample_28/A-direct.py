import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    participants = ["participant_0", "participant_1", "participant_2",
                    "participant_3", "participant_4", "participant_5",
                    "participant_6"]
    cars = ["car_0", "car_1", "car_2", "car_3", "car_4", "car_5"]

    preferences = {
        "participant_0": ["car_2"],
        "participant_1": ["car_0"],
        "participant_2": ["car_0", "car_1"],
        "participant_3": ["car_1"],
        "participant_4": ["car_1"],
        "participant_5": [],
        "participant_6": ["car_3"],
    }

    edges = [(p, c) for p in participants for c in preferences[p]]

    # Precompute edge lists to avoid trivial constraints when no edges exist
    edges_by_participant = {p: [c for (pp, c) in edges if pp == p] for p in participants}
    edges_by_car = {c: [p for (p, cc) in edges if cc == c] for c in cars}

    model = pyo.ConcreteModel()

    model.E = pyo.Set(initialize=edges, dimen=2)
    model.x = pyo.Var(model.E, domain=pyo.Binary)

    def obj_rule(m):
        return sum(m.x[p, c] for (p, c) in m.E)

    model.total_assignments = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    # Each participant assigned to at most one car
    def participant_rule(m, p):
        c_list = edges_by_participant[p]
        if not c_list:
            return pyo.Constraint.Skip
        return sum(m.x[p, c] for c in c_list) <= 1

    model.participant_constraint = pyo.Constraint(
        [p for p in participants if edges_by_participant[p]], rule=participant_rule
    )

    # Each car assigned to at most one participant
    def car_rule(m, c):
        p_list = edges_by_car[c]
        if not p_list:
            return pyo.Constraint.Skip
        return sum(m.x[p, c] for p in p_list) <= 1

    model.car_constraint = pyo.Constraint(
        [c for c in cars if edges_by_car[c]], rule=car_rule
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_assignments))
    return {"objective": obj_val, "status": "optimal"}