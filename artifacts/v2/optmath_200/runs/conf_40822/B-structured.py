# IR: {"sets":{"I":["participant_0","participant_1","participant_2","participant_3"],"J":["car_0","car_1","car_2","car_3","car_4"]},"params":{"assignment_allowance":"a[i,j] binary, from params","participant_assignment_capacity":"b[i] nonnegative, from params","car_assignment_capacity":"c[j] nonnegative, from params"},"variables":{"x[i,j]":"binary"},"constraints":["x[i,j] <= a[i,j] for all i,j","sum(j in J) x[i,j] <= b[i] for all i","sum(i in I) x[i,j] <= c[j] for all j"],"objective":"maximize sum(i in I,j in J) x[i,j]"}
from collections.abc import Mapping

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _entry(data, label, position):
    """Accept sequences or mappings keyed by labels or integer positions."""
    if isinstance(data, Mapping):
        if label in data:
            return data[label]
        return data[position]
    return data[position]


def solve(params):
    participants = tuple(f"participant_{idx}" for idx in range(4))
    cars = tuple(f"car_{idx}" for idx in range(5))

    allowance_input = params["assignment_allowance"]
    participant_capacity_input = params["participant_assignment_capacity"]
    car_capacity_input = params["car_assignment_capacity"]

    allowance = {}
    for participant_position, participant in enumerate(participants):
        row = _entry(allowance_input, participant, participant_position)
        for car_position, car in enumerate(cars):
            allowance[participant, car] = _entry(row, car, car_position)

    participant_capacity = {
        participant: _entry(
            participant_capacity_input, participant, participant_position
        )
        for participant_position, participant in enumerate(participants)
    }
    car_capacity = {
        car: _entry(car_capacity_input, car, car_position)
        for car_position, car in enumerate(cars)
    }

    model = pyo.ConcreteModel()
    model.participants = pyo.Set(initialize=participants, ordered=True)
    model.cars = pyo.Set(initialize=cars, ordered=True)

    model.assignment_allowance = pyo.Param(
        model.participants,
        model.cars,
        initialize=allowance,
        within=pyo.Binary,
    )
    model.participant_assignment_capacity = pyo.Param(
        model.participants,
        initialize=participant_capacity,
        within=pyo.NonNegativeReals,
    )
    model.car_assignment_capacity = pyo.Param(
        model.cars,
        initialize=car_capacity,
        within=pyo.NonNegativeReals,
    )

    model.assignment = pyo.Var(
        model.participants, model.cars, domain=pyo.Binary
    )

    def eligibility_rule(instance, participant, car):
        return (
            instance.assignment[participant, car]
            <= instance.assignment_allowance[participant, car]
        )

    model.eligibility_constraints = pyo.Constraint(
        model.participants, model.cars, rule=eligibility_rule
    )

    def participant_capacity_rule(instance, participant):
        return (
            sum(instance.assignment[participant, car] for car in instance.cars)
            <= instance.participant_assignment_capacity[participant]
        )

    model.participant_capacity_constraints = pyo.Constraint(
        model.participants, rule=participant_capacity_rule
    )

    def car_capacity_rule(instance, car):
        return (
            sum(
                instance.assignment[participant, car]
                for participant in instance.participants
            )
            <= instance.car_assignment_capacity[car]
        )

    model.car_capacity_constraints = pyo.Constraint(
        model.cars, rule=car_capacity_rule
    )

    model.total_assignments = pyo.Objective(
        expr=sum(
            model.assignment[participant, car]
            for participant in model.participants
            for car in model.cars
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solver_failed"}

    try:
        obj_val = float(pyo.value(model.total_assignments))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}