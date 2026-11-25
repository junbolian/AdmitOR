# IR: {"sets":{"participants":"0..7","cars":"0..6"},"params":{"preferences":"binary[participants,cars], from params","participant_capacity":"nonnegative scalar, from params","car_capacity":"nonnegative scalar, from params"},"variables":{"assignment[participant,car]":"binary"},"constraints":["assignment[participant,car] <= preferences[participant,car] for each participant,car","sum_car assignment[participant,car] <= participant_capacity for each participant","sum_participant assignment[participant,car] <= car_capacity for each car"],"objective":"maximize sum_participant,car assignment[participant,car]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    preferences = params["preferences"]
    participant_capacity = params["participant_capacity"]
    car_capacity = params["car_capacity"]

    model = pyo.ConcreteModel()
    model.participants = pyo.RangeSet(0, 7)
    model.cars = pyo.RangeSet(0, 6)

    model.preferences = pyo.Param(
        model.participants,
        model.cars,
        initialize=lambda instance, participant, car: preferences[participant][car],
        within=pyo.Binary,
    )
    model.participant_capacity = pyo.Param(
        initialize=participant_capacity,
        within=pyo.NonNegativeReals,
    )
    model.car_capacity = pyo.Param(
        initialize=car_capacity,
        within=pyo.NonNegativeReals,
    )

    model.assignment = pyo.Var(
        model.participants,
        model.cars,
        domain=pyo.Binary,
    )

    def eligibility_rule(instance, participant, car):
        return (
            instance.assignment[participant, car]
            <= instance.preferences[participant, car]
        )

    model.eligibility_constraints = pyo.Constraint(
        model.participants,
        model.cars,
        rule=eligibility_rule,
    )

    def participant_limit_rule(instance, participant):
        return (
            sum(
                instance.assignment[participant, car]
                for car in instance.cars
            )
            <= instance.participant_capacity
        )

    model.participant_limits = pyo.Constraint(
        model.participants,
        rule=participant_limit_rule,
    )

    def car_limit_rule(instance, car):
        return (
            sum(
                instance.assignment[participant, car]
                for participant in instance.participants
            )
            <= instance.car_capacity
        )

    model.car_limits = pyo.Constraint(
        model.cars,
        rule=car_limit_rule,
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
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_assignments))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}