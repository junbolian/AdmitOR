# IR: {"sets":{"participants":"range(params['participant_count'])","cars":"range(params['car_count'])"},"params":{"participant_count":"nonnegative integer; frozen","car_count":"nonnegative integer; frozen","preference":"binary matrix indexed by participant, car","participant_capacity":"nonnegative vector indexed by participant, or scalar broadcast to all participants","car_capacity":"nonnegative vector indexed by car, or scalar broadcast to all cars","assignment_value":"real scalar"},"variables":{"assignment[participant,car]":"binary"},"constraints":["assignment[participant,car] <= preference[participant,car] for every participant and car","sum(assignment[participant,car] for car in cars) <= participant_capacity[participant] for every participant","sum(assignment[participant,car] for participant in participants) <= car_capacity[car] for every car"],"objective":"maximize assignment_value * sum(assignment[participant,car] for every participant and car)"}

from numbers import Real

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    participant_count = params["participant_count"]
    car_count = params["car_count"]
    preference = params["preference"]
    participant_capacity = params["participant_capacity"]
    car_capacity = params["car_capacity"]
    assignment_value = params["assignment_value"]

    def indexed_capacity(values, position):
        return values if isinstance(values, Real) else values[position]

    model = pyo.ConcreteModel()

    model.participants = pyo.Set(
        initialize=range(participant_count),
        ordered=True,
    )
    model.cars = pyo.Set(
        initialize=range(car_count),
        ordered=True,
    )

    model.preference = pyo.Param(
        model.participants,
        model.cars,
        initialize=lambda mdl, participant, car: preference[participant][car],
        within=pyo.Binary,
    )
    model.participant_capacity = pyo.Param(
        model.participants,
        initialize=lambda mdl, participant: indexed_capacity(
            participant_capacity, participant
        ),
        within=pyo.NonNegativeReals,
    )
    model.car_capacity = pyo.Param(
        model.cars,
        initialize=lambda mdl, car: indexed_capacity(car_capacity, car),
        within=pyo.NonNegativeReals,
    )
    model.assignment_value = pyo.Param(
        initialize=assignment_value,
        within=pyo.Reals,
    )

    model.assignment = pyo.Var(
        model.participants,
        model.cars,
        domain=pyo.Binary,
    )

    model.preference_limits = pyo.Constraint(
        model.participants,
        model.cars,
        rule=lambda mdl, participant, car: (
            mdl.assignment[participant, car]
            <= mdl.preference[participant, car]
        ),
    )

    def participant_limit_rule(mdl, participant):
        return (
            None,
            pyo.quicksum(
                mdl.assignment[participant, car]
                for car in mdl.cars
            ),
            mdl.participant_capacity[participant],
        )

    model.participant_limits = pyo.Constraint(
        model.participants,
        rule=participant_limit_rule,
    )

    def car_limit_rule(mdl, car):
        return (
            None,
            pyo.quicksum(
                mdl.assignment[participant, car]
                for participant in mdl.participants
            ),
            mdl.car_capacity[car],
        )

    model.car_limits = pyo.Constraint(
        model.cars,
        rule=car_limit_rule,
    )

    model.total_assignment_value = pyo.Objective(
        expr=model.assignment_value
        * pyo.quicksum(
            model.assignment[participant, car]
            for participant in model.participants
            for car in model.cars
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as exc:
        if "A feasible solution was not found" in str(exc):
            return {"objective": None, "status": "no_feasible_solution"}
        raise

    try:
        obj_val = float(pyo.value(model.total_assignment_value))
    except ValueError:
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}