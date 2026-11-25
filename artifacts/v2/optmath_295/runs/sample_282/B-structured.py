# IR: {"sets":{"P":"range(num_participants)","C":"range(num_cars)"},"params":{"num_participants":"params['num_participants']","num_cars":"params['num_cars']","preference[i,j]":"params[f'preference_{i}_{j}'] for i,j in range(6)"},"variables":{"assignment[i,j]":"Binary for i in P, j in C"},"constraints":["For each i in P: sum(assignment[i,j] for j in C) <= 1","For each j in C: sum(assignment[i,j] for i in P) <= 1","For each i in P, j in C: assignment[i,j] <= preference[i,j]"],"objective":"maximize sum(assignment[i,j] for i in P, j in C)"}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_participants = params["num_participants"]
    num_cars = params["num_cars"]
    preferences = {
        (participant, car): params[f"preference_{participant}_{car}"]
        for participant in range(6)
        for car in range(6)
    }

    model = pyo.ConcreteModel()

    model.participants = pyo.Set(
        initialize=range(num_participants), ordered=True
    )
    model.cars = pyo.Set(
        initialize=range(num_cars), ordered=True
    )

    model.preference = pyo.Param(
        model.participants,
        model.cars,
        initialize=lambda mdl, participant, car: preferences[participant, car],
        within=pyo.Binary,
    )

    model.assignment = pyo.Var(
        model.participants,
        model.cars,
        domain=pyo.Binary,
    )

    def participant_limit_rule(mdl, participant):
        # A three-element tuple specifies lower bound, expression, upper bound.
        return (
            None,
            pyo.quicksum(
                mdl.assignment[participant, car] for car in mdl.cars
            ),
            1,
        )

    model.participant_limit = pyo.Constraint(
        model.participants, rule=participant_limit_rule
    )

    def car_limit_rule(mdl, car):
        return (
            None,
            pyo.quicksum(
                mdl.assignment[participant, car]
                for participant in mdl.participants
            ),
            1,
        )

    model.car_limit = pyo.Constraint(
        model.cars, rule=car_limit_rule
    )

    def willingness_rule(mdl, participant, car):
        return (
            mdl.assignment[participant, car]
            <= mdl.preference[participant, car]
        )

    model.willingness_limit = pyo.Constraint(
        model.participants,
        model.cars,
        rule=willingness_rule,
    )

    model.total_assignments = pyo.Objective(
        expr=pyo.quicksum(
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