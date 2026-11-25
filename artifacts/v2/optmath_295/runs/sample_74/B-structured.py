# IR: {"sets":{"participants":"range(num_participants)","cars":"range(num_cars)"},"params":["num_participants","num_cars","assignment_value","participant_capacity","car_capacity","preference_matrix"],"variables":{"assignment[i,j]":"binary for i in participants, j in cars"},"constraints":["assignment[i,j] <= preference_matrix[i][j] for all i,j","sum_j assignment[i,j] <= participant_capacity for all i","sum_i assignment[i,j] <= car_capacity for all j"],"objective":"maximize assignment_value * sum_i sum_j assignment[i,j]"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_participants = params["num_participants"]
    num_cars = params["num_cars"]
    assignment_value = params["assignment_value"]
    participant_capacity = params["participant_capacity"]
    car_capacity = params["car_capacity"]
    preference_matrix = params["preference_matrix"]

    model = pyo.ConcreteModel()

    model.participants = pyo.Set(
        initialize=range(num_participants), ordered=True
    )
    model.cars = pyo.Set(initialize=range(num_cars), ordered=True)

    model.assignment_value = pyo.Param(initialize=assignment_value)
    model.participant_capacity = pyo.Param(initialize=participant_capacity)
    model.car_capacity = pyo.Param(initialize=car_capacity)
    model.eligibility = pyo.Param(
        model.participants,
        model.cars,
        initialize=lambda mdl, participant, car: (
            preference_matrix[participant][car]
        ),
    )

    model.assignment = pyo.Var(
        model.participants, model.cars, domain=pyo.Binary
    )

    def eligibility_rule(mdl, participant, car):
        return (
            mdl.assignment[participant, car]
            <= mdl.eligibility[participant, car]
        )

    model.preference_constraints = pyo.Constraint(
        model.participants, model.cars, rule=eligibility_rule
    )

    def participant_capacity_rule(mdl, participant):
        return (
            pyo.quicksum(
                mdl.assignment[participant, car] for car in mdl.cars
            )
            <= mdl.participant_capacity
        )

    model.participant_constraints = pyo.Constraint(
        model.participants, rule=participant_capacity_rule
    )

    def car_capacity_rule(mdl, car):
        return (
            pyo.quicksum(
                mdl.assignment[participant, car]
                for participant in mdl.participants
            )
            <= mdl.car_capacity
        )

    model.car_constraints = pyo.Constraint(
        model.cars, rule=car_capacity_rule
    )

    model.total_value = pyo.Objective(
        expr=model.assignment_value
        * pyo.quicksum(
            model.assignment[participant, car]
            for participant in model.participants
            for car in model.cars
        ),
        sense=pyo.maximize,
    )

    # Appsi raises RuntimeError when it cannot load a feasible solution.
    # Objective retrieval remains the sole test for success.
    solve_failed = False
    try:
        Highs().solve(model)
    except RuntimeError:
        solve_failed = True

    try:
        obj_val = float(pyo.value(model.total_value))
    except (ValueError, TypeError):
        return {
            "objective": None,
            "status": (
                "solve_failed" if solve_failed else "objective_unavailable"
            ),
        }

    return {"objective": obj_val, "status": "optimal"}