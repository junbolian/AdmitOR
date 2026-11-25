# IR: {"sets":{"participants":"participant_i, i in range(params[n_participants])","cars":"car_j, j in range(params[n_cars])"},"params":{"n_participants":"scalar or singleton list","n_cars":"scalar or singleton list","car_capacity":"scalar, singleton list, or car-indexed list","participant_capacity":"scalar, singleton list, or participant-indexed list","objective_coefficient":"scalar, singleton list, or participant-car matrix; scalar entries broadcast"},"variables":{"assignment[p,c]":"Binary"},"constraints":["For each participant p: sum_c assignment[p,c] <= participant_capacity[p]","For each car c: sum_p assignment[p,c] <= car_capacity[c]","For every pair except (participant_1,car_1) and (participant_1,car_2): assignment[p,c] = 0"],"objective":"maximize sum_{p,c} objective_coefficient[p,c] * assignment[p,c]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _parameter_value(data, *indices):
    """Unwrap singleton lists and index nonsingleton parameter lists."""
    remaining = iter(indices)
    while isinstance(data, (list, tuple)):
        if len(data) == 1:
            data = data[0]
        elif not data:
            raise ValueError("Parameter lists must not be empty.")
        else:
            try:
                position = next(remaining)
            except StopIteration:
                raise ValueError(
                    "Expected a scalar or singleton parameter value."
                ) from None
            data = data[position]
    return data


def solve(params):
    n_participants = int(_parameter_value(params["n_participants"]))
    n_cars = int(_parameter_value(params["n_cars"]))
    car_capacity_data = params["car_capacity"]
    participant_capacity_data = params["participant_capacity"]
    objective_coefficient_data = params["objective_coefficient"]

    participant_names = [
        f"participant_{idx}" for idx in range(n_participants)
    ]
    car_names = [f"car_{idx}" for idx in range(n_cars)]

    model = pyo.ConcreteModel()

    model.participants = pyo.Set(
        initialize=participant_names, ordered=True
    )
    model.cars = pyo.Set(initialize=car_names, ordered=True)

    model.car_capacity = pyo.Param(
        model.cars,
        initialize={
            car: _parameter_value(car_capacity_data, car_idx)
            for car_idx, car in enumerate(car_names)
        },
        within=pyo.Reals,
        mutable=True,
    )
    model.participant_capacity = pyo.Param(
        model.participants,
        initialize={
            participant: _parameter_value(
                participant_capacity_data, participant_idx
            )
            for participant_idx, participant in enumerate(participant_names)
        },
        within=pyo.Reals,
        mutable=True,
    )
    model.objective_coefficient = pyo.Param(
        model.participants,
        model.cars,
        initialize={
            (participant, car): _parameter_value(
                objective_coefficient_data, participant_idx, car_idx
            )
            for participant_idx, participant in enumerate(participant_names)
            for car_idx, car in enumerate(car_names)
        },
        within=pyo.Reals,
    )

    model.assignment = pyo.Var(
        model.participants, model.cars, domain=pyo.Binary
    )

    def participant_limit_rule(model, participant):
        return (
            pyo.quicksum(
                model.assignment[participant, car] for car in model.cars
            )
            <= model.participant_capacity[participant]
        )

    model.participant_limits = pyo.Constraint(
        model.participants, rule=participant_limit_rule
    )

    def car_limit_rule(model, car):
        return (
            pyo.quicksum(
                model.assignment[participant, car]
                for participant in model.participants
            )
            <= model.car_capacity[car]
        )

    model.car_limits = pyo.Constraint(
        model.cars, rule=car_limit_rule
    )

    def preference_rule(model, participant, car):
        if participant == "participant_1" and car in ("car_1", "car_2"):
            return pyo.Constraint.Skip
        return model.assignment[participant, car] == 0

    model.preference_limits = pyo.Constraint(
        model.participants, model.cars, rule=preference_rule
    )

    model.total_profit = pyo.Objective(
        expr=pyo.quicksum(
            model.objective_coefficient[participant, car]
            * model.assignment[participant, car]
            for participant in model.participants
            for car in model.cars
        ),
        sense=pyo.maximize,
    )

    failure_reason = "objective_unavailable"
    try:
        Highs().solve(model)
    except RuntimeError:
        failure_reason = "solve_failed"

    try:
        obj_val = float(pyo.value(model.total_profit))
    except (ValueError, TypeError):
        return {"objective": None, "status": failure_reason}

    return {"objective": obj_val, "status": "optimal"}