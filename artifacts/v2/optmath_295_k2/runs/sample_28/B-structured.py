# IR: {"sets":{"participants":[0,1,2,3,4,5,6],"cars":[0,1,2,3,4,5],"preferred_pairs":[[0,2],[1,0],[2,0],[2,1],[3,1],[4,1],[6,3]]},"params":{},"variables":{"assignment[i,j]":{"domain":"Binary","indices":"preferred_pairs"}},"constraints":["For each participant i: sum(assignment[i,j] for preferred pairs incident to i) <= 1.","For each car j: sum(assignment[i,j] for preferred pairs incident to j) <= 1."],"objective":{"sense":"maximize","expression":"sum(assignment[i,j] for (i,j) in preferred_pairs)"}}

import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # The problem declares no numeric parameters; all data are structural.
    model = pyo.ConcreteModel()

    model.participants = pyo.Set(initialize=range(7), ordered=True)
    model.cars = pyo.Set(initialize=range(6), ordered=True)
    model.preferred_pairs = pyo.Set(
        dimen=2,
        initialize=[
            (0, 2),
            (1, 0),
            (2, 0),
            (2, 1),
            (3, 1),
            (4, 1),
            (6, 3),
        ],
        ordered=True,
    )

    model.assignment = pyo.Var(model.preferred_pairs, domain=pyo.Binary)

    def participant_limit_rule(problem, participant):
        # Tuple form also supports participants with no preferred cars.
        return (
            None,
            pyo.quicksum(
                problem.assignment[participant, car]
                for car in problem.cars
                if (participant, car) in problem.preferred_pairs
            ),
            1,
        )

    model.participant_limit = pyo.Constraint(
        model.participants, rule=participant_limit_rule
    )

    def car_limit_rule(problem, car):
        return (
            None,
            pyo.quicksum(
                problem.assignment[participant, car]
                for participant in problem.participants
                if (participant, car) in problem.preferred_pairs
            ),
            1,
        )

    model.car_limit = pyo.Constraint(model.cars, rule=car_limit_rule)

    model.total_assignments = pyo.Objective(
        expr=pyo.quicksum(
            model.assignment[participant, car]
            for participant, car in model.preferred_pairs
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