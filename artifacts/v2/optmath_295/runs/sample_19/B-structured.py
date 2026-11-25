# IR: {"sets":{"P":"range(num_participants)","C":"range(num_cars)"},"params":{"num_participants":"params['num_participants']","num_cars":"params['num_cars']","preference_weights":"params['preference_weights'][i][j], binary; unspecified entries are 0","participant_capacity":"params['participant_capacity']","car_capacity":"params['car_capacity']","assignment_value":"params['assignment_value']"},"variables":{"assignment[i,j]":"Binary for i in P, j in C"},"constraints":["sum(assignment[i,j] for j in C) <= participant_capacity for i in P","sum(assignment[i,j] for i in P) <= car_capacity for j in C","assignment[i,j] <= preference_weights[i,j] for i in P, j in C"],"objective":"maximize assignment_value * sum(assignment[i,j] for i in P, j in C)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_participants = params["num_participants"]
    num_cars = params["num_cars"]
    preference_weights = params["preference_weights"]
    participant_capacity = params["participant_capacity"]
    car_capacity = params["car_capacity"]
    assignment_value = params["assignment_value"]

    model = pyo.ConcreteModel()

    model.participants = pyo.Set(
        initialize=range(num_participants), ordered=True
    )
    model.cars = pyo.Set(initialize=range(num_cars), ordered=True)

    model.allowed_assignment = pyo.Param(
        model.participants,
        model.cars,
        initialize={
            (participant, car): preference_weights[participant][car]
            for participant in range(num_participants)
            for car in range(num_cars)
        },
        within=pyo.Binary,
        default=0,
    )
    model.participant_limit = pyo.Param(
        initialize=participant_capacity, within=pyo.NonNegativeReals
    )
    model.car_limit = pyo.Param(
        initialize=car_capacity, within=pyo.NonNegativeReals
    )
    model.assignment_reward = pyo.Param(
        initialize=assignment_value, within=pyo.Reals
    )

    model.assignment = pyo.Var(
        model.participants, model.cars, domain=pyo.Binary
    )

    def participant_capacity_rule(current_model, participant):
        return (
            sum(
                current_model.assignment[participant, car]
                for car in current_model.cars
            )
            <= current_model.participant_limit
        )

    model.participant_constraints = pyo.Constraint(
        model.participants, rule=participant_capacity_rule
    )

    def car_capacity_rule(current_model, car):
        return (
            sum(
                current_model.assignment[participant, car]
                for participant in current_model.participants
            )
            <= current_model.car_limit
        )

    model.car_constraints = pyo.Constraint(
        model.cars, rule=car_capacity_rule
    )

    def preference_rule(current_model, participant, car):
        return (
            current_model.assignment[participant, car]
            <= current_model.allowed_assignment[participant, car]
        )

    model.preference_constraints = pyo.Constraint(
        model.participants, model.cars, rule=preference_rule
    )

    model.total_assignment_value = pyo.Objective(
        expr=model.assignment_reward
        * sum(
            model.assignment[participant, car]
            for participant in model.participants
            for car in model.cars
        ),
        sense=pyo.maximize,
    )

    solve_failed = False
    try:
        Highs().solve(model)
    except RuntimeError:
        solve_failed = True

    try:
        obj_val = float(pyo.value(model.total_assignment_value))
    except ValueError:
        return {
            "objective": None,
            "status": (
                "infeasible_or_failed"
                if solve_failed
                else "objective_unavailable"
            ),
        }

    return {"objective": obj_val, "status": "optimal"}