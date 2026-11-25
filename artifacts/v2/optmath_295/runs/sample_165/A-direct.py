import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    participant_count = int(params["participant_count"])
    car_count = int(params["car_count"])

    pref_keys = [
        ("participant_0_pref_car_1", 0, 1),
        ("participant_1_pref_car_5", 1, 5),
        ("participant_2_pref_car_3", 2, 3),
        ("participant_4_pref_car_1", 4, 1),
        ("participant_4_pref_car_4", 4, 4),
        ("participant_4_pref_car_5", 4, 5),
        ("participant_5_pref_car_4", 5, 4),
    ]

    allowed = []
    for key, p, c in pref_keys:
        val = params[key]
        if val is not None and float(val) >= 0.5:
            if (p, c) not in allowed:
                allowed.append((p, c))

    model = pyo.ConcreteModel()

    model.x = pyo.Var(allowed, domain=pyo.Binary)

    def obj_rule(m):
        return sum(m.x[p, c] for (p, c) in allowed)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    def participant_rule(m, p):
        terms = [m.x[pp, c] for (pp, c) in allowed if pp == p]
        if not terms:
            return pyo.Constraint.Feasible
        return sum(terms) <= 1

    model.participant_con = pyo.Constraint(
        range(participant_count), rule=participant_rule
    )

    def car_rule(m, c):
        terms = [m.x[p, cc] for (p, cc) in allowed if cc == c]
        if not terms:
            return pyo.Constraint.Feasible
        return sum(terms) <= 1

    model.car_con = pyo.Constraint(range(car_count), rule=car_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}