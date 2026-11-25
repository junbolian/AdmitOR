import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    num_participants = int(params["num_participants"])
    num_cars = int(params["num_cars"])

    participant_set = pyo.RangeSet(0, num_participants - 1)
    car_set = pyo.RangeSet(0, num_cars - 1)
    link_set = pyo.Set(
        dimen=2,
        initialize=[
            (p_idx, c_idx)
            for p_idx in range(num_participants)
            for c_idx in range(num_cars)
        ],
    )

    assignment_value = params["assignment_value"]

    pref_keys = [
        ("preference_p0_c5", 0, 5),
        ("preference_p1_c2", 1, 2),
        ("preference_p1_c3", 1, 3),
        ("preference_p2_c4", 2, 4),
    ]

    interest = {}
    for p_idx in range(num_participants):
        for c_idx in range(num_cars):
            interest[(p_idx, c_idx)] = 0.0
    for key, p_idx, c_idx in pref_keys:
        interest[(p_idx, c_idx)] = params[key]
    for key, p_idx in [
        ("preference_p3_any", 3),
        ("preference_p4_any", 4),
        ("preference_p5_any", 5),
    ]:
        if p_idx < num_participants:
            for c_idx in range(num_cars):
                interest[(p_idx, c_idx)] = params[key]

    model.assign = pyo.Var(link_set, domain=pyo.Binary)

    def objective_rule(mdl):
        return sum(
            assignment_value * interest[(p_idx, c_idx)] * mdl.assign[p_idx, c_idx]
            for (p_idx, c_idx) in link_set
        )

    model.total_value = pyo.Objective(rule=objective_rule, sense=pyo.maximize)

    def participant_rule(mdl, p_idx):
        return sum(mdl.assign[p_idx, c_idx] for c_idx in car_set) <= 1

    model.participant_limit = pyo.Constraint(participant_set, rule=participant_rule)

    def car_rule(mdl, c_idx):
        return sum(mdl.assign[p_idx, c_idx] for p_idx in participant_set) <= 1

    model.car_limit = pyo.Constraint(car_set, rule=car_rule)

    def preference_rule(mdl, p_idx, c_idx):
        return mdl.assign[p_idx, c_idx] <= interest[(p_idx, c_idx)]

    model.preference_limit = pyo.Constraint(link_set, rule=preference_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_value))
    return {"objective": obj_val, "status": "optimal"}