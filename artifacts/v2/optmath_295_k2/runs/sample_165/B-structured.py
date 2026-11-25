# IR: {"sets":{"participants":"range(num_participants)","cars":"range(num_cars)"},"params":{"preference_matrix":"binary[participants,cars]","assignment_capacity_per_participant":"nonnegative scalar","assignment_capacity_per_car":"nonnegative scalar","num_participants":"nonnegative integer; frozen index size","num_cars":"nonnegative integer; frozen index size","objective_weight_per_assignment":"real scalar"},"variables":{"assignment[participants,cars]":"binary"},"constraints":["For each participant: sum_car assignment[participant,car] <= assignment_capacity_per_participant","For each car: sum_participant assignment[participant,car] <= assignment_capacity_per_car","For each participant,car: assignment[participant,car] <= preference_matrix[participant,car]"],"objective":"maximize objective_weight_per_assignment * sum_participant,car assignment[participant,car]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    model = pyo.ConcreteModel()

    model.num_participants = pyo.Param(
        initialize=params["num_participants"],
        within=pyo.NonNegativeIntegers,
        mutable=False,
    )
    model.num_cars = pyo.Param(
        initialize=params["num_cars"],
        within=pyo.NonNegativeIntegers,
        mutable=False,
    )

    model.participants = pyo.Set(
        initialize=range(pyo.value(model.num_participants)),
        ordered=True,
    )
    model.cars = pyo.Set(
        initialize=range(pyo.value(model.num_cars)),
        ordered=True,
    )

    model.preference = pyo.Param(
        model.participants,
        model.cars,
        initialize=lambda mdl, participant, car: params["preference_matrix"][
            participant
        ][car],
        within=pyo.Binary,
    )
    model.participant_capacity = pyo.Param(
        initialize=params["assignment_capacity_per_participant"],
        within=pyo.NonNegativeReals,
    )
    model.car_capacity = pyo.Param(
        initialize=params["assignment_capacity_per_car"],
        within=pyo.NonNegativeReals,
    )
    model.assignment_weight = pyo.Param(
        initialize=params["objective_weight_per_assignment"],
        within=pyo.Reals,
    )

    model.assignment = pyo.Var(
        model.participants,
        model.cars,
        domain=pyo.Binary,
    )

    def participant_capacity_rule(mdl, participant):
        return (
            sum(mdl.assignment[participant, car] for car in mdl.cars)
            <= mdl.participant_capacity
        )

    model.participant_capacity_constraints = pyo.Constraint(
        model.participants,
        rule=participant_capacity_rule,
    )

    def car_capacity_rule(mdl, car):
        return (
            sum(
                mdl.assignment[participant, car]
                for participant in mdl.participants
            )
            <= mdl.car_capacity
        )

    model.car_capacity_constraints = pyo.Constraint(
        model.cars,
        rule=car_capacity_rule,
    )

    def preference_rule(mdl, participant, car):
        return (
            mdl.assignment[participant, car]
            <= mdl.preference[participant, car]
        )

    model.preference_constraints = pyo.Constraint(
        model.participants,
        model.cars,
        rule=preference_rule,
    )

    model.total_value = pyo.Objective(
        expr=model.assignment_weight
        * sum(
            model.assignment[participant, car]
            for participant in model.participants
            for car in model.cars
        ),
        sense=pyo.maximize,
    )

    try:
        Highs().solve(model)
    except RuntimeError as error:
        # APPsi raises this when it cannot load a feasible solution.
        # Let unrelated, unexpected solver errors propagate.
        if "a feasible solution was not found" not in str(error).lower():
            raise

    try:
        obj_val = float(pyo.value(model.total_value))
    except ValueError:
        return {"objective": None, "status": "no_objective"}

    return {"objective": obj_val, "status": "optimal"}