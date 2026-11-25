# IR: {"sets":{"P":"range(params['num_participants'])","C":"range(params['num_cars'])","A":"{(i,j) in P x C: j in preferences[i]}"},"params":["participant_0_preferred_car_3","participant_1_preferred_car_1","participant_2_preferred_cars_1_3","participant_3_preferred_cars_2_4","participant_4_preferred_cars_3_5","participant_5_preferred_cars_2_6","participant_6_preferred_car_6","assignment_capacity_per_participant","assignment_capacity_per_car","num_participants","num_cars","assignment_variable_domain"],"variables":{"assignment[i,j]":"Binary for (i,j) in A; assignment_variable_domain must specify Binary or {0,1}"},"constraints":["For each i in P: sum(assignment[i,j] for j with (i,j) in A) <= assignment_capacity_per_participant; empty sum is zero.","For each j in C: sum(assignment[i,j] for i with (i,j) in A) <= assignment_capacity_per_car; empty sum is zero.","Disallowed assignment pairs have no decision variables."],"objective":"maximize sum(assignment[i,j] for (i,j) in A)"}

import operator
from numbers import Integral

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    participant_count = operator.index(params["num_participants"])
    car_count = operator.index(params["num_cars"])
    participant_capacity = params["assignment_capacity_per_participant"]
    car_capacity = params["assignment_capacity_per_car"]
    domain_specification = params["assignment_variable_domain"]

    preference_keys = (
        "participant_0_preferred_car_3",
        "participant_1_preferred_car_1",
        "participant_2_preferred_cars_1_3",
        "participant_3_preferred_cars_2_4",
        "participant_4_preferred_cars_3_5",
        "participant_5_preferred_cars_2_6",
        "participant_6_preferred_car_6",
    )
    raw_preferences = [params[key] for key in preference_keys]

    if participant_count != len(preference_keys):
        return {"objective": None, "status": "invalid_participant_count"}

    if car_count < 0:
        return {"objective": None, "status": "invalid_car_count"}

    if isinstance(domain_specification, str):
        valid_domain = domain_specification.strip().lower() == "binary"
    else:
        valid_domain = set(domain_specification) == {0, 1}

    if not valid_domain:
        return {"objective": None, "status": "invalid_binary_domain"}

    preferences = {}
    for participant, raw_preference in enumerate(raw_preferences):
        if isinstance(raw_preference, Integral):
            preferred_cars = (operator.index(raw_preference),)
        else:
            preferred_cars = tuple(
                operator.index(car) for car in raw_preference
            )

        if any(car < 0 or car >= car_count for car in preferred_cars):
            return {"objective": None, "status": "invalid_preference"}

        preferences[participant] = tuple(sorted(set(preferred_cars)))

    allowed_pairs = [
        (participant, car)
        for participant in range(participant_count)
        for car in preferences[participant]
    ]
    interested_participants = {
        car: [
            participant
            for participant in range(participant_count)
            if car in preferences[participant]
        ]
        for car in range(car_count)
    }

    model = pyo.ConcreteModel()
    model.participants = pyo.Set(
        initialize=range(participant_count), ordered=True
    )
    model.cars = pyo.Set(initialize=range(car_count), ordered=True)
    model.allowed_pairs = pyo.Set(
        dimen=2, initialize=allowed_pairs, ordered=True
    )
    model.participant_capacity = pyo.Param(
        initialize=participant_capacity, within=pyo.Reals
    )
    model.car_capacity = pyo.Param(
        initialize=car_capacity, within=pyo.Reals
    )
    model.assignment = pyo.Var(
        model.allowed_pairs, domain=pyo.Binary
    )

    def participant_limit_rule(instance, participant):
        # Tuple form remains valid when the sum contains no variables.
        return (
            None,
            pyo.quicksum(
                instance.assignment[participant, car]
                for car in preferences[participant]
            ),
            instance.participant_capacity,
        )

    def car_limit_rule(instance, car):
        # Preserve 0 <= capacity even for cars with no interested participants.
        return (
            None,
            pyo.quicksum(
                instance.assignment[participant, car]
                for participant in interested_participants[car]
            ),
            instance.car_capacity,
        )

    model.participant_limits = pyo.Constraint(
        model.participants, rule=participant_limit_rule
    )
    model.car_limits = pyo.Constraint(
        model.cars, rule=car_limit_rule
    )
    model.total_assignments = pyo.Objective(
        expr=pyo.quicksum(
            model.assignment[participant, car]
            for participant, car in model.allowed_pairs
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_assignments))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}