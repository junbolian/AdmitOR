import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_participants = int(params["num_participants"])
    num_cars = int(params["num_cars"])
    interest = params["participant_car_interest"]
    max_participant_assignments = int(params["max_participant_assignments"])
    max_car_assignments = int(params["max_car_assignments"])

    participants = list(range(num_participants))
    cars = list(range(num_cars))

    model = pyo.ConcreteModel()

    # Only create variables for eligible (participant, car) pairs
    eligible_pairs = [
        (p, c)
        for p in participants
        for c in cars
        if int(interest[p][c]) == 1
    ]

    if not eligible_pairs:
        return {"objective": 0.0, "status": "optimal"}

    model.assign = pyo.Var(eligible_pairs, domain=pyo.Binary)

    model.objective = pyo.Objective(
        expr=sum(model.assign[p, c] for (p, c) in eligible_pairs),
        sense=pyo.maximize,
    )

    # Build lookup of valid pairs to avoid trivial-Boolean issues in rules
    eligible_set = set(eligible_pairs)

    def participant_rule(m, p):
        terms = [m.assign[p, c] for (pp, c) in eligible_pairs if pp == p]
        if not terms:
            return pyo.Constraint.Skip
        return sum(terms) <= max_participant_assignments

    def car_rule(m, c):
        terms = [m.assign[p, cc] for (p, cc) in eligible_pairs if cc == c]
        if not terms:
            return pyo.Constraint.Skip
        return sum(terms) <= max_car_assignments

    model.participant_limit = pyo.Constraint(participants, rule=participant_rule)
    model.car_limit = pyo.Constraint(cars, rule=car_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.objective))
    return {"objective": obj_val, "status": "optimal"}