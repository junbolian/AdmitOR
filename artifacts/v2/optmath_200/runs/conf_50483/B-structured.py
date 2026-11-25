# IR: {"sets":{"P":[0,1,2,3,4],"C":[0,1,2,3]},"params":{"participant_preferences":"binary[P,C]","max_assignments_per_participant":"nonnegative scalar or vector[P]","max_participants_per_car":"nonnegative scalar or vector[C]","objective_coefficients":"real scalar or matrix[P,C]"},"variables":{"assignment[P,C]":"binary"},"constraints":["assignment[p,c] <= participant_preferences[p,c] for all p,c","sum(c in C, assignment[p,c]) <= max_assignments_per_participant[p] for all p","sum(p in P, assignment[p,c]) <= max_participants_per_car[c] for all c"],"objective":"maximize sum(p in P,c in C, objective_coefficients[p,c]*assignment[p,c])"}

from collections.abc import Mapping
from numbers import Number

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def _entry(data, *indices):
    """Read a scalar, nested sequence/mapping, or tuple-keyed mapping."""
    if isinstance(data, Number):
        return data

    if isinstance(data, Mapping) and len(indices) > 1 and indices in data:
        return data[indices]

    value = data
    for position in indices:
        value = value[position]
    return value


def solve(params):
    preferences = params["participant_preferences"]
    participant_capacities = params["max_assignments_per_participant"]
    car_capacities = params["max_participants_per_car"]
    rewards = params["objective_coefficients"]

    model = pyo.ConcreteModel()
    model.participants = pyo.RangeSet(0, 4)
    model.cars = pyo.RangeSet(0, 3)

    model.preference = pyo.Param(
        model.participants,
        model.cars,
        within=pyo.Binary,
        initialize=lambda model, participant, car: _entry(
            preferences, participant, car
        ),
    )
    model.participant_capacity = pyo.Param(
        model.participants,
        within=pyo.NonNegativeReals,
        initialize=lambda model, participant: _entry(
            participant_capacities, participant
        ),
    )
    model.car_capacity = pyo.Param(
        model.cars,
        within=pyo.NonNegativeReals,
        initialize=lambda model, car: _entry(car_capacities, car),
    )
    model.reward = pyo.Param(
        model.participants,
        model.cars,
        within=pyo.Reals,
        initialize=lambda model, participant, car: _entry(
            rewards, participant, car
        ),
    )

    model.assignment = pyo.Var(
        model.participants, model.cars, domain=pyo.Binary
    )

    model.preference_constraint = pyo.Constraint(
        model.participants,
        model.cars,
        rule=lambda model, participant, car: (
            model.assignment[participant, car]
            <= model.preference[participant, car]
        ),
    )
    model.participant_capacity_constraint = pyo.Constraint(
        model.participants,
        rule=lambda model, participant: (
            sum(
                model.assignment[participant, car]
                for car in model.cars
            )
            <= model.participant_capacity[participant]
        ),
    )
    model.car_capacity_constraint = pyo.Constraint(
        model.cars,
        rule=lambda model, car: (
            sum(
                model.assignment[participant, car]
                for participant in model.participants
            )
            <= model.car_capacity[car]
        ),
    )

    model.total_reward = pyo.Objective(
        expr=sum(
            model.reward[participant, car]
            * model.assignment[participant, car]
            for participant in model.participants
            for car in model.cars
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "a feasible solution was not found" in str(exc).lower():
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_reward))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}