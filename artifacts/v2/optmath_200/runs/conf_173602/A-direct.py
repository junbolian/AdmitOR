import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _as_scalar(val):
    if isinstance(val, (list, tuple)):
        if len(val) == 1:
            return val[0]
        return sum(val)
    return val


def solve(params):
    n_participants = int(params["n_participants"])
    n_cars = int(params["n_cars"])
    car_capacity = float(_as_scalar(params["car_capacity"]))
    participant_capacity = float(_as_scalar(params["participant_capacity"]))
    objective_coefficient = float(_as_scalar(params["objective_coefficient"]))

    participants = list(range(n_participants))
    cars = list(range(n_cars))

    # Preference/eligibility structure: participant_1 -> {car_1, car_2}, others -> none
    allowed = {}
    for p in participants:
        if p == 1:
            allowed[p] = [c for c in cars if c in (1, 2)]
        else:
            allowed[p] = []

    model = pyo.ConcreteModel()

    model.P = pyo.Set(initialize=participants, ordered=True)
    model.C = pyo.Set(initialize=cars, ordered=True)

    pairs = [(p, c) for p in participants for c in allowed[p]]

    model.x = pyo.Var(pairs, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(objective_coefficient * model.x[p, c] for (p, c) in pairs),
        sense=pyo.maximize,
    )

    # Each participant assigned to at most participant_capacity cars
    def participant_rule(m, p):
        terms = [m.x[p, c] for c in allowed[p]]
        if not terms:
            return pyo.Constraint.Skip
        return sum(terms) <= participant_capacity

    model.participant_limit = pyo.Constraint(model.P, rule=participant_rule)

    # Each car assigned to at most car_capacity participants
    def car_rule(m, c):
        terms = [m.x[p, c] for p in participants if c in allowed[p]]
        if not terms:
            return pyo.Constraint.Skip
        return sum(terms) <= car_capacity

    model.car_limit = pyo.Constraint(model.C, rule=car_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}