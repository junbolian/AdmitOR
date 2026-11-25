import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_participants = int(params["num_participants"])
    num_cars = int(params["num_cars"])
    participant_capacity = params["participant_capacity"]
    car_capacity = params["car_capacity"]
    assignment_coefficient = params["assignment_coefficient"]

    participants = list(range(num_participants))
    cars = list(range(num_cars))

    pref = {}
    for p in participants:
        for c in cars:
            key = "pref_" + str(p) + "_" + str(c)
            if key in params and params[key] != 0:
                pref[(p, c)] = params[key]

    allowed_pairs = list(pref.keys())

    model = pyo.ConcreteModel()

    model.PAIRS = pyo.Set(initialize=allowed_pairs, dimen=2)
    model.PARTICIPANTS = pyo.Set(initialize=participants)
    model.CARS = pyo.Set(initialize=cars)

    model.x = pyo.Var(model.PAIRS, domain=pyo.Binary)

    model.obj = pyo.Objective(
        expr=sum(assignment_coefficient * model.x[p, c] for (p, c) in allowed_pairs),
        sense=pyo.maximize,
    )

    pairs_by_p = {p: [c for (pp, c) in allowed_pairs if pp == p] for p in participants}
    pairs_by_c = {c: [p for (p, cc) in allowed_pairs if cc == c] for c in cars}

    def participant_rule(mdl, p):
        cars_p = pairs_by_p[p]
        if not cars_p:
            return pyo.Constraint.Skip
        return sum(mdl.x[p, c] for c in cars_p) <= participant_capacity

    def car_rule(mdl, c):
        parts_c = pairs_by_c[c]
        if not parts_c:
            return pyo.Constraint.Skip
        return sum(mdl.x[p, c] for p in parts_c) <= car_capacity

    model.participant_limit = pyo.Constraint(model.PARTICIPANTS, rule=participant_rule)
    model.car_limit = pyo.Constraint(model.CARS, rule=car_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}