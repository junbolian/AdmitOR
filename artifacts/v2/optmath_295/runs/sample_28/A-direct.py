import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    car_capacity = params["car_capacity"]
    participant_assignment_limit = params["participant_assignment_limit"]

    participants = [f"participant_{i}" for i in range(7)]
    cars = [f"car_{i}" for i in range(6)]

    preferences = {
        "participant_0": ["car_2"],
        "participant_1": ["car_0"],
        "participant_2": ["car_0", "car_1"],
        "participant_3": ["car_1"],
        "participant_4": ["car_1"],
        "participant_5": [],
        "participant_6": ["car_3"],
    }

    pairs = [(p, c) for p in participants for c in preferences[p]]

    model = pyo.ConcreteModel()
    model.P = pyo.Set(initialize=participants)
    model.C = pyo.Set(initialize=cars)
    model.PAIRS = pyo.Set(initialize=pairs, dimen=2)

    model.x = pyo.Var(model.PAIRS, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(model.x[p, c] for (p, c) in pairs),
        sense=pyo.maximize,
    )

    def participant_rule(m, p):
        prefs = preferences[p]
        if not prefs:
            return pyo.Constraint.Feasible
        return sum(m.x[p, c] for c in prefs) <= participant_assignment_limit

    model.participant_limit = pyo.Constraint(model.P, rule=participant_rule)

    def car_rule(m, c):
        interested = [p for p in participants if c in preferences[p]]
        if not interested:
            return pyo.Constraint.Feasible
        return sum(m.x[p, c] for p in interested) <= car_capacity

    model.car_limit = pyo.Constraint(model.C, rule=car_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}