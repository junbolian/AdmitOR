# {
#   "sets": {"P": "range(num_participants)", "C": "range(num_cars)", "E": "{(i,j) in P x C : j in preferences[i]}"},
#   "params": ["num_participants", "num_cars", "preferences"],
#   "variables": {"x[i,j]": "Binary for (i,j) in E", "assigned_total": "NonNegativeIntegers"},
#   "constraints": [
#     "Participant capacity: sum(x[i,j] for j with (i,j) in E) <= 1 for each i in P",
#     "Car capacity: sum(x[i,j] for i with (i,j) in E) <= 1 for each j in C",
#     "Assignment count: assigned_total == sum(x[i,j] for (i,j) in E)"
#   ],
#   "objective": "maximize assigned_total"
# }

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_participants = params["num_participants"]
    num_cars = params["num_cars"]
    preferences = params["preferences"]

    participant_indices = range(num_participants)
    car_indices = range(num_cars)

    allowed_pairs = [
        (participant, car)
        for participant in participant_indices
        for car in car_indices
        if car in preferences[participant]
    ]

    cars_by_participant = {
        participant: [] for participant in participant_indices
    }
    participants_by_car = {car: [] for car in car_indices}

    for participant, car in allowed_pairs:
        cars_by_participant[participant].append(car)
        participants_by_car[car].append(participant)

    model = pyo.ConcreteModel()
    model.P = pyo.Set(initialize=participant_indices, ordered=True)
    model.C = pyo.Set(initialize=car_indices, ordered=True)
    model.E = pyo.Set(dimen=2, initialize=allowed_pairs, ordered=True)

    # Only preferred participant-car pairs have assignment variables.
    model.x = pyo.Var(model.E, domain=pyo.Binary)

    # This variable also keeps the model solvable when E is empty.
    model.assigned_total = pyo.Var(domain=pyo.NonNegativeIntegers)

    def participant_capacity_rule(block, participant):
        expression = pyo.quicksum(
            block.x[participant, car]
            for car in cars_by_participant[participant]
        )
        return (None, expression, 1)

    model.participant_capacity = pyo.Constraint(
        model.P, rule=participant_capacity_rule
    )

    def car_capacity_rule(block, car):
        expression = pyo.quicksum(
            block.x[participant, car]
            for participant in participants_by_car[car]
        )
        return (None, expression, 1)

    model.car_capacity = pyo.Constraint(model.C, rule=car_capacity_rule)

    model.assignment_count = pyo.Constraint(
        expr=model.assigned_total
        == pyo.quicksum(
            model.x[participant, car]
            for participant, car in model.E
        )
    )

    model.assignment_objective = pyo.Objective(
        expr=model.assigned_total,
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.assignment_objective))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}