import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # Structural constants
    participants = list(range(7))
    cars = list(range(7))

    # Eligibility data with corresponding parameter keys
    eligible_pairs = [
        (0, 0, "participant_0_pref_car_0"),
        (0, 5, "participant_0_pref_car_5"),
        (0, 6, "participant_0_pref_car_6"),
        (2, 1, "participant_2_pref_car_1"),
        (2, 3, "participant_2_pref_car_3"),
        (2, 6, "participant_2_pref_car_6"),
        (3, 1, "participant_3_pref_car_1"),
        (3, 5, "participant_3_pref_car_5"),
        (3, 6, "participant_3_pref_car_6"),
        (4, 3, "participant_4_pref_car_3"),
        (5, 0, "participant_5_pref_car_0"),
        (5, 6, "participant_5_pref_car_6"),
        (6, 0, "participant_6_pref_car_0"),
    ]

    assignment_value = params["assignment_value"]
    participant_capacity = params["participant_capacity"]
    car_capacity = params["car_capacity"]

    # Only include pairs that are eligible (coefficient nonzero)
    active_pairs = [
        (p, c) for (p, c, key) in eligible_pairs
        if params[key] != 0
    ]

    model = pyo.ConcreteModel()

    # Indexed set of allowed (participant, car) assignments
    model.allowed = pyo.Set(initialize=active_pairs, dimen=2)

    model.x = pyo.Var(model.allowed, domain=pyo.Binary)

    # Objective: maximize number of successful assignments
    model.total_assigned = pyo.Objective(
        expr=sum(assignment_value * model.x[p, c] for (p, c) in active_pairs),
        sense=pyo.maximize,
    )

    # One car per participant (at most participant_capacity)
    def participant_rule(mdl, p):
        allowed_for_p = [c for (pp, c) in active_pairs if pp == p]
        if not allowed_for_p:
            return pyo.Constraint.Feasible
        return sum(mdl.x[p, c] for c in allowed_for_p) <= participant_capacity

    model.participant_limit = pyo.Constraint(participants, rule=participant_rule)

    # One participant per car (at most car_capacity)
    def car_rule(mdl, c):
        allowed_for_c = [p for (p, cc) in active_pairs if cc == c]
        if not allowed_for_c:
            return pyo.Constraint.Feasible
        return sum(mdl.x[p, c] for p in allowed_for_c) <= car_capacity

    model.car_limit = pyo.Constraint(cars, rule=car_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_assigned))
    return {"objective": obj_val, "status": "optimal"}